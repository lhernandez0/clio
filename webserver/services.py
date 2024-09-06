import spacy
from elasticsearch_dsl import Search
from sentence_transformers import SentenceTransformer

# Load NLP models
nlp = spacy.load("en_core_web_md")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def semantic_search(query: str):
    # Perform semantic search using Hugging Face and SentenceTransformers
    vector = embedding_model.encode(query).tolist()
    s = Search(index="rss_feeds").knn(
        field="embedding", k=5, num_candidates=10, query_vector=vector
    )
    response = s.execute()
    results = [
        {
            "title": hit.title,
            "summary": hit.summary,
            "similarity": nlp(query).similarity(nlp(hit.summary)),
        }
        for hit in response
    ]
    return results


def text_search(query: str):
    # Perform text search using Elasticsearch DSL
    s = Search(index="rss_feeds").query("match", summary=query)
    response = s.execute()
    results = [{"title": hit.title, "summary": hit.summary} for hit in response]
    return results
