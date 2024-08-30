import logging
from datetime import datetime, timedelta

import spacy
from airflow.operators.python import PythonOperator
from hooks.elasticsearch_hook import ElasticsearchHook
from spacy.language import Language

from airflow import DAG

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
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("spacytextblob")
    nlp.add_pipe("filter_entities", after="spacytextblob")
    logger.info("Successfully loaded spaCy model 'en_core_web_sm' with custom components")
except Exception as e:
    logger.error(f"Error loading spaCy model: {e}")
    raise

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 28),
    "retries": 5,
    "retry_delay": timedelta(minutes=3),
}


def process_articles_with_nlp():
    es = ElasticsearchHook()
    try:
        articles = es.get_new_articles(index="rss_feeds")
        logger.info(f"Retrieved {len(articles)} new articles from Elasticsearch")
    except Exception as e:
        logger.error(f"Error retrieving articles from Elasticsearch: {e}")
        return

    for article in articles:
        try:
            doc = nlp(article["_source"]["summary"])
            entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
            sentiment = (
                doc._.blob.sentiment.polarity
            )  # Using spacytextblob for sentiment analysis

            enriched_data = {
                "nlp_processed": True,
                "entities": entities,
                "sentiment": sentiment,
            }

            es.update_article(index="rss_feeds", id=article["_id"], body=enriched_data)
            logger.info(f"Enriched data: {enriched_data}")
            logger.info(f"Successfully processed and updated article: {article['_id']}")
        except Exception as e:
            logger.error(f"Error processing article ID: {article['_id']}, Error: {e}")


dag = DAG(
    "nlp_article_processing_dag",
    default_args=default_args,
    description="A DAG to process articles with NLP tasks from RSS feeds",
    schedule_interval="30 * * * *",  # Runs every hour at 30th minute
)

nlp_processing_task = PythonOperator(
    task_id="process_articles_with_nlp_task",
    python_callable=process_articles_with_nlp,
    dag=dag,
)
