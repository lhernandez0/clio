from typing import Any, Dict, List

import spacy
from bs4 import BeautifulSoup
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


def clean_summary(summary):
    # Parse the HTML content
    soup = BeautifulSoup(summary, "html.parser")
    # Extract text, removing all HTML tags
    cleaned_text = soup.get_text(separator=" ")
    return cleaned_text


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

            # Clean the summary text
            self.summary = clean_summary(self.summary)

            # Process entities with spaCy
            doc = nlp(self.summary)
            relevant_labels = {
                "PERSON",
                "ORG",
                "GPE",
                "LOC",
                "EVENT",
                "MONEY",
                "PRODUCT",
                "WORK_OF_ART",
            }
            self.entities = [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
                if ent.label_ in relevant_labels
            ]

            self.nlp_processed = True
