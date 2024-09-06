from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from webserver.config import get_es_connection
from webserver.services import semantic_search, text_search


async def lifespan(app: FastAPI):
    # Startup event
    get_es_connection()
    yield  # Application will run after this point
    # Shutdown event (cleanup code if needed)
    # e.g., closing connections or cleaning up resources


app = FastAPI(lifespan=lifespan)


@app.get("/search/semantic/")
async def semantic_search_endpoint(query: str):
    results = semantic_search(query)
    return {"results": results}


@app.get("/search/text/")
async def text_search_endpoint(query: str):
    results = text_search(query)
    return {"results": results}


# Redirect root URL to Swagger UI
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
