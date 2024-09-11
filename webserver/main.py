from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Query, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from common.utils.logger import setup_logging
from models.openai import ChatRequest
from webserver import clients
from webserver.config import get_es_connection
from webserver.services import (
    get_trending_entities,
    semantic_search,
    stream_chatgpt_response,
    text_search,
)
from webserver.utils import get_default_dates

# Set up logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup event
    get_es_connection()
    await clients.openai_client_setup()
    yield
    # Shutdown event
    await clients.open_ai_client_teardown()


app = FastAPI(lifespan=lifespan)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="webserver/static"), name="static")


@app.get("/search/semantic/")
async def semantic_search_endpoint(
    query: str,
    page: Optional[int] = Query(default=1, ge=1),
    size: Optional[int] = Query(default=10, ge=1),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    # If no date range is provided, use the current date
    if not start_date or not end_date:
        start_date, end_date = get_default_dates()

    results = semantic_search(query, start_date, end_date, page, size)
    return {"results": results}


@app.get("/search/text/")
async def text_search_endpoint(
    query: str,
    page: Optional[int] = Query(default=1, ge=1),
    size: Optional[int] = Query(default=10, ge=1),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    # If no date range is provided, use the current date
    if not start_date or not end_date:
        start_date, end_date = get_default_dates()

    results = text_search(query, start_date, end_date, page, size)
    return {"results": results}


@app.get("/search/trending/")
async def trending_entities_endpoint(
    days: int = Query(
        default=1, description="Number of days to consider for trending entities"
    ),
    size: int = Query(default=10, description="Number of trending entities to return"),
):
    results = get_trending_entities(days=days, size=size)
    return {"results": results}


@app.post("/chat/")
async def chatgpt_with_messages(request: ChatRequest, stream: bool = True):
    # Prepare the messages to send to ChatGPT
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # Get context from semantic_search_endpoint with 1 year date range
    start_date = date.today() - timedelta(days=365)
    end_date = date.today()
    logger.debug(f"Semantic search query: {request.messages[-1].content}")
    semantic_search_results = semantic_search(
        query=request.messages[-1].content,
        start_date=start_date,
        end_date=end_date,
        page=1,
        size=5,
    )
    logger.debug(f"semantic_search_results: {semantic_search_results}")
    # Get streamed response from ChatGPT
    chat_response = await stream_chatgpt_response(
        messages, stream=stream, es_context=semantic_search_results
    )

    return {"chat_response": chat_response}


# WebSocket route for streaming ChatGPT responses
@app.websocket("/ws/chat/")
async def chatgpt_with_messages_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        # Receive the request messages from the WebSocket
        data = await websocket.receive_json()

        # Prepare the messages to send to ChatGPT
        messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in data["messages"]
        ]

        # Perform semantic search as in the POST route
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        logger.info(f"Semantic search query: {messages[-1]['content']}")
        semantic_search_results = semantic_search(
            query=messages[-1]["content"],
            start_date=start_date,
            end_date=end_date,
            page=1,
            size=5,
        )
        logger.debug(f"semantic_search_results: {semantic_search_results}")

        # Stream the ChatGPT response via WebSocket
        async for chunk in stream_chatgpt_response(
            messages, stream=True, es_context=semantic_search_results, websocket=websocket
        ):
            # Send each chunk through the WebSocket
            await websocket.send_text(chunk)
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        await websocket.send_text("An error occurred.")
    finally:
        await websocket.close()


# # Redirect root URL to Swagger UI
# @app.get("/")
# async def root():
#     return RedirectResponse(url="/docs")


# Serve the main HTML file at the root
@app.get("/")
async def read_root():
    return FileResponse("webserver/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
