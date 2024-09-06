from datetime import date

import spacy
from elasticsearch_dsl import Search
from sentence_transformers import SentenceTransformer

# Load NLP models
nlp = spacy.load("en_core_web_md")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def semantic_search(query: str, start_date: date, end_date: date):
    # Perform semantic search using Hugging Face and SentenceTransformers
    vector = embedding_model.encode(query).tolist()
    s = (
        Search(index="rss_feeds")
        .knn(field="embedding", k=5, num_candidates=10, query_vector=vector)
        .filter("range", published={"gte": start_date, "lte": end_date})
    )  # Add date range filter
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
            "similarity": nlp(query).similarity(nlp(hit.summary)),
        }
        for hit in response
    ]
    return results


def text_search(query: str, start_date: date, end_date: date):
    # Perform text search using Elasticsearch DSL
    s = (
        Search(index="rss_feeds")
        .query("match", summary=query)
        .filter("range", published={"gte": start_date, "lte": end_date})
    )  # Add date range filter
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
