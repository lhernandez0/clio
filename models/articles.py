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

# Constants for model selection
SENTIMENT_MODEL = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SPACY_MODEL = "en_core_web_md"

# Load models
sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL, device=-1)
embedding_model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
nlp = spacy.load(SPACY_MODEL)

# Relevant named entity labels
RELEVANT_LABELS = {
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "EVENT",
    "MONEY",
    "PRODUCT",
    "WORK_OF_ART",
}


def clean_text(html_text: str) -> str:
    """Removes HTML tags and returns clean text."""
    return BeautifulSoup(html_text, "html.parser").get_text(separator=" ")


def analyze_sentiment(text: str) -> float:
    """Returns sentiment score from -1 (negative) to 1 (positive)."""
    result = sentiment_pipeline(text[:512])
    if result[0]["label"] == "NEGATIVE":
        return -result[0]["score"]
    return result[0]["score"]


def generate_embedding(text: str) -> List[float]:
    """Generates an embedding vector for the given text."""
    return embedding_model.encode(text).tolist()


def extract_entities(text: str) -> List[Dict[str, Any]]:
    """Extracts relevant named entities from the text."""
    doc = nlp(text)
    return [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in RELEVANT_LABELS
    ]


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
            self.summary = clean_text(self.summary)
            self.sentiment = analyze_sentiment(self.summary)
            self.embedding = generate_embedding(self.summary)
            self.entities = extract_entities(self.summary)
            self.nlp_processed = True


if __name__ == "__main__":
    sample_text = """
        WASHINGTON – Volodymyr Zelensky said Friday that his relations with the United States can still be repaired, after President Donald Trump shouted at him in an angry White House meltdown accusing the Ukrainian leader of refusing to make peace with Russia. “Of course,” Zelensky said when asked in a Fox News interview if the relationship with Trump could be salvaged. US-Ukrainian ties are about “more than two presidents,” he said, adding that Ukraine badly needs Washington’s help in the fight against Russia’s far bigger and better-armed military. “It will be difficult without your support,” Zelensky said on Fox — […]... Keep on reading:  Zelensky says Trump relationship can be repaired after White House row
        """

    article = Article(summary=sample_text)
    article.clean()

    print("Cleaned Summary:", article.summary)
    print("Sentiment Score:", article.sentiment)
    print("Embedding Vector (first 5 values):", article.embedding[:5])
    print("Extracted Entities:", article.entities)
