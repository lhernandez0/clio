import logging
from datetime import datetime
from typing import Any, Dict, List

import feedparser
import spacy
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from elasticsearch import ConnectionError, NotFoundError, TransportError
from elasticsearch.helpers import BulkIndexError, bulk
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
from hooks.elasticsearch_hook import ElasticsearchHook
from requests.exceptions import RequestException
from spacy.language import Language
from spacytextblob.spacytextblob import SpacyTextBlob  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define custom component to filter entities
@Language.component("filter_entities")
def filter_entities(doc):
    RELEVANT_LABELS = {
        "PERSON",
        "ORG",
        "GPE",
        "LOC",
        # "DATE", # Removing DATE due to noise
        "EVENT",
        "MONEY",
        "PRODUCT",
        "WORK_OF_ART",
    }
    doc.ents = [ent for ent in doc.ents if ent.label_ in RELEVANT_LABELS]
    return doc


# Load the NLP model
try:
    nlp = spacy.load("en_core_web_md")
    nlp.add_pipe("spacytextblob")
    nlp.add_pipe("filter_entities", after="spacytextblob")
    logger.info("Successfully loaded spaCy model 'en_core_web_sm' with custom components")
except Exception as e:
    logger.error(f"Error loading spaCy model: {e}")
    raise


class Article(Document):
    title: str = Text()
    link: str = Keyword()
    published: str = Date()
    summary: str = Text()
    source: str = Keyword()
    embedding: List[float] = DenseVector(dims=300, similarity="cosine")
    nlp_processed: bool = Boolean()
    entities: List[Dict[str, Any]] = Nested(
        properties={"text": Text(), "label": Keyword()}
    )
    sentiment: float = Float()

    class Index:
        name = "rss_feeds"

    def clean(self):
        if not self.embedding:
            doc = nlp(self.summary)
            self.entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
            self.sentiment = (
                doc._.blob.sentiment.polarity
            )  # Using spacytextblob for sentiment analysis
            self.nlp_processed = True
            self.embedding = doc.vector.tolist()


class FetchRSSFeedOperator(BaseOperator):

    @apply_defaults
    def __init__(self, feed_url, es_index, outlet_name, *args, **kwargs):
        super(FetchRSSFeedOperator, self).__init__(*args, **kwargs)
        self.feed_url = feed_url
        self.es_index = es_index
        self.outlet_name = outlet_name
        self.es = ElasticsearchHook()
        self.logger = logging.getLogger(__name__)

    def execute(self, context):
        self.logger.info("Starting to process feed: %s", self.feed_url)

        try:
            # Parsing the RSS feed
            parsed_feed = feedparser.parse(self.feed_url)

            if not parsed_feed.entries:
                self.logger.warning(f"No entries found in feed: {self.feed_url}")
                return

            actions = []
            for entry in parsed_feed.entries:
                try:
                    # Check if the article already exists
                    if not self.es.exists(index=self.es_index, id=entry.link):
                        # Parse the published date
                        try:
                            published_date = datetime.strptime(
                                entry.published, "%a, %d %b %Y %H:%M:%S %z"
                            )
                        except ValueError:
                            self.logger.warning(
                                f"Could not parse date for entry {entry.link}. Using current time."
                            )
                            published_date = datetime.now()

                        # Create an Article instance
                        article = Article(
                            meta={"id": entry.link},
                            title=entry.get("title", ""),
                            link=entry.link,
                            published=published_date,
                            summary=entry.get("summary", ""),
                            source=self.outlet_name,
                            nlp_processed=False,
                        )

                        article.clean()

                        # Add to actions for bulk indexing
                        actions.append(article.to_dict(include_meta=True))
                    else:
                        self.logger.debug(f"Document with ID {entry.link} already exists")

                except Exception as e:
                    self.logger.error(f"Error processing entry {entry.link}: {str(e)}")
                    # Continue processing other entries
                    continue

            if actions:
                try:
                    # Bulk indexing
                    success, failed = bulk(
                        self.es.es, actions, index=self.es_index, raise_on_error=False
                    )
                    self.logger.info(f"Indexed {success} documents")
                    if failed:
                        self.logger.warning(f"Failed to index {len(failed)} documents")
                        for item in failed:
                            self.logger.error(f"Failed to index document: {item}")
                except BulkIndexError as e:
                    self.logger.error(f"Bulk indexing error: {str(e)}")
                except (NotFoundError, ConnectionError, TransportError) as e:
                    self.logger.error(f"Elasticsearch error: {str(e)}")
                    raise
            else:
                self.logger.info("No new documents to index")

        except RequestException as e:
            self.logger.error(
                f"Network error when fetching feed {self.feed_url}: {str(e)}"
            )
            raise
        except feedparser.FeedParserError as e:
            self.logger.error(f"Error parsing feed {self.feed_url}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error processing feed {self.feed_url}: {str(e)}"
            )
            raise
