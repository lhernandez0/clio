from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

from webserver.config import get_es_connection
from webserver.services import semantic_search, text_search
from webserver.utils import get_default_dates


async def lifespan(app: FastAPI):
    # Startup event
    get_es_connection()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/search/semantic/")
async def semantic_search_endpoint(
    query: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    # If no date range is provided, use the current date
    if not start_date or not end_date:
        start_date, end_date = get_default_dates()

    results = semantic_search(query, start_date, end_date)
    return {"results": results}


@app.get("/search/text/")
async def text_search_endpoint(
    query: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    # If no date range is provided, use the current date
    if not start_date or not end_date:
        start_date, end_date = get_default_dates()

    results = text_search(query, start_date, end_date)
    return {"results": results}


# Redirect root URL to Swagger UI
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
