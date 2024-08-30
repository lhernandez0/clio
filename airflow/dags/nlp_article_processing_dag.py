import logging
import os
from datetime import datetime, timedelta

import spacy
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from hooks.elasticsearch_hook import ElasticsearchHook
from spacy.language import Language
from spacytextblob.spacytextblob import SpacyTextBlob  # noqa: F401
from utils.utils import generate_dag_list

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


# Define the DAG
config_dir = os.path.join(os.getcwd(), "config", "news_outlets")
rss_ingestion_dag_ids = generate_dag_list(config_dir)

dag = DAG(
    "nlp_article_processing_dag",
    default_args=default_args,
    description="A DAG to process articles with NLP tasks from RSS feeds",
    schedule_interval="0 * * * *",  # Runs at the start of every hour
)

# Create a list to hold the sensors
sensors = []

# Add ExternalTaskSensors to ensure the DAG waits for all specified RSS ingestion DAGs to complete
for dag_id, _ in rss_ingestion_dag_ids:
    sensor_task_id = f"wait_for_{dag_id}_completion"

    sensor = ExternalTaskSensor(
        task_id=sensor_task_id,
        external_dag_id=dag_id,
        external_task_id=None,  # None means wait for the whole DAG
        mode="poke",
        timeout=900,  # Wait for 15 minutes
        poke_interval=60,  # Check every 60 seconds
        dag=dag,
    )

    sensors.append(sensor)

# Define a EmptyOperator to serve as a downstream task for sensors
waiting_end_sensor = EmptyOperator(
    task_id="waiting_end_sensor",
    dag=dag,
    trigger_rule="all_done",  # Runs when all upstream tasks are done
)

# Define the nlp_processing_task
nlp_processing_task = PythonOperator(
    task_id="process_articles_with_nlp_task",
    python_callable=process_articles_with_nlp,
    dag=dag,
)

# Set dependencies
for sensor in sensors:
    sensor >> waiting_end_sensor

# Ensure nlp_processing_task runs after all sensors (regardless of their status)
waiting_end_sensor >> nlp_processing_task
