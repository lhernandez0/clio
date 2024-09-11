from datetime import datetime, timedelta
from typing import List

import spacy
from elasticsearch_dsl import Q, Search
from fastapi import WebSocket
from sentence_transformers import SentenceTransformer

from common.utils.logger import setup_logging
from webserver.clients import get_openai_client
from webserver.config import get_prompts

# Set up logging
logger = setup_logging()

# Load NLP models
nlp = spacy.load("en_core_web_md")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def semantic_search(query: str, start_date: str, end_date: str, page: int, size: int):
    # Perform semantic search using Hugging Face and SentenceTransformers
    vector = embedding_model.encode(query).tolist()

    # Calculate the offset for pagination
    from_value = (page - 1) * size

    # Create the date range filter
    date_filter = Q("range", published={"gte": start_date, "lte": end_date})

    # Build the search query with pagination using slicing
    s = Search(index="rss_feeds").query(
        Q(
            "knn",
            field="embedding",
            k=5,
            num_candidates=10,
            query_vector=vector,
            filter=date_filter,
        )
    )[
        from_value : from_value + size
    ]  # Use slicing for pagination

    logger.debug(s.to_dict())

    response = s.execute()

    # Include all relevant fields in the results
    results = [
        {
            "title": hit.title,
            "summary": hit.summary,
            "link": hit.link,
            "published": hit.published,
            "source": hit.source,
            "entities": hit.entities if hasattr(hit, "entities") else None,
            "sentiment": hit.sentiment,
            "nlp_processed": hit.nlp_processed,
            "similarity": nlp(query).similarity(nlp(hit.summary)),
        }
        for hit in response
    ]
    return results


def text_search(query: str, start_date: str, end_date: str, page: int, size: int):
    # Calculate the offset for pagination
    from_value = (page - 1) * size

    # Perform text search using Elasticsearch DSL
    s = (
        Search(index="rss_feeds")
        .query("match", summary=query)
        .filter("range", published={"gte": start_date, "lte": end_date})[
            from_value : from_value + size
        ]  # Use slicing for pagination
    )

    logger.debug(s.to_dict())

    response = s.execute()

    # Include all relevant fields in the results
    results = [
        {
            "title": hit.title,
            "summary": hit.summary,
            "link": hit.link,
            "published": hit.published,
            "source": hit.source,
            "entities": hit.entities,
            "sentiment": hit.sentiment,
            "nlp_processed": hit.nlp_processed,
        }
        for hit in response
    ]
    return results


def get_trending_entities(
    index="rss_feeds", field="entities.text.keyword", days=1, size=10
):
    # Define the time range (e.g., last 24 hours)
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    end_date = datetime.now().isoformat()

    # Build the search query
    s = Search(index=index)
    s = s.filter("range", published={"gte": start_date, "lte": end_date})

    # Add the aggregation
    s.aggs.bucket("trending_entities", "terms", field=field, size=size)

    # Execute the search
    response = s.execute()

    # Return the buckets from the aggregation
    return response.aggregations.trending_entities.buckets


# Update stream_chatgpt_response to handle both WebSockets and regular requests
async def stream_chatgpt_response(
    messages: List[dict],
    stream: bool = True,
    es_context: List = None,
    websocket: WebSocket = None,
) -> str:
    openai_client = await get_openai_client()
    if openai_client is None:
        logger.error("OpenAI client is not initialized.")
        raise ValueError("OpenAI client is not initialized.")

    # Get prompts from config
    prompts = get_prompts()

    # Insert system instructions at the beginning
    messages.insert(0, {"role": "system", "content": prompts["system_instructions"]})

    # Insert context about current date and time
    current_datetime = datetime.now().strftime("%A, %d %B %Y %I:%M %p")
    date_time_context = "It's currently " + current_datetime
    messages.insert(1, {"role": "system", "content": date_time_context})

    # logger.info(f"ChatGPT request: {messages}")
    for message in messages:
        logger.debug(f"ChatGPT request: {message}")

    # Add the ES context to the messages
    if es_context:
        logger.info(f"Using ES context with {len(es_context)} articles.")
        es_content = prompts["es_context_prompt"]
        es_content = es_content.format(
            articles="\n\n".join(
                [
                    f"- Title: {hit['title']}\n  Summary: {hit['summary']}\n  Link: {hit['link']}\n  Published: {hit['published']}\n  Source: {hit['source']}"
                    for hit in es_context
                ]
            )
        )
        messages.append({"role": "system", "content": es_content})
    else:
        # No ES articles found
        messages.append({"role": "system", "content": prompts["no_es_context_prompt"]})

    # Add the safety prompt
    messages.append({"role": "system", "content": prompts["safety_prompt"]})

    logger.info(f"ChatGPT request: {messages}")
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=stream,
    )

    response = ""
    async for chunk in stream:
        content = chunk.choices[0].delta.content or ""

        # If WebSocket is provided, stream each chunk over WebSocket
        if websocket:
            await websocket.send_text(content)
        else:
            response += content

    if not websocket:
        logger.info(f"ChatGPT response: {response}")
        return response
