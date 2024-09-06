from typing import Any, Dict, List

import spacy
from elasticsearch_dsl import (
    Boolean,
    Date,
    DenseVector,
    Document,
    Float,
    Keyword,
    Nested,
    Text,
)
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Load the sentiment analysis and embedding models
model_name = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
sentiment_pipeline = pipeline(
    "sentiment-analysis", model=model_name, device=-1
)  # device=-1 ensures CPU usage
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2", device="cpu"
)  # Ensure CPU usage
nlp = spacy.load("en_core_web_md")  # Load the spaCy model


class Article(Document):
    title: str = Text()
    link: str = Keyword()
    published: str = Date()
    summary: str = Text()
    source: str = Keyword()
    embedding: List[float] = DenseVector(dims=384, similarity="cosine")
    nlp_processed: bool = Boolean()
    entities: List[Dict[str, Any]] = Nested(
        properties={"text": Text(), "label": Keyword()}
    )
    sentiment: float = Float()

    class Index:
        name = "rss_feeds"

    def clean(self):
        if not self.embedding:
            # Use Hugging Face for sentiment analysis
            sentiment_result = sentiment_pipeline(
                self.summary[:512]
            )  # Truncate to 512 tokens if necessary
            self.sentiment = sentiment_result[0]["score"] if sentiment_result else 0.0

            # Use SentenceTransformers for embeddings
            self.embedding = embedding_model.encode(self.summary).tolist()

            # Process entities with spaCy
            doc = nlp(self.summary)
            self.entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

            self.nlp_processed = True
