from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

from webserver.config import get_es_connection
from webserver.services import get_trending_entities, semantic_search, text_search
from webserver.utils import get_default_dates


async def lifespan(app: FastAPI):
    # Startup event
    get_es_connection()
    yield


app = FastAPI(lifespan=lifespan)


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


# Redirect root URL to Swagger UI
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
