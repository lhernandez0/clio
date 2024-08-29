import json
import logging
import os
from datetime import datetime, timedelta

from operators.rss_feed_operator import FetchRSSFeedOperator

from airflow import DAG

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 28),
    "retries": 5,
    "retry_delay": timedelta(minutes=3),
}

dag = DAG(
    "rss_ingestion_dag",
    default_args=default_args,
    description="A DAG to ingest RSS feeds from major news outlets",
    schedule_interval=timedelta(minutes=60),  # Runs every hour
)

logger = logging.getLogger(__name__)


# Function to create tasks dynamically
def create_rss_tasks(json_file):
    logger.info("Creating tasks from JSON file: %s", json_file)
    try:
        with open(json_file, "r") as f:
            feeds = json.load(f)
            outlet_name = feeds.get("name")
            if not outlet_name:
                logger.warning("No 'name' field found in JSON file: %s", json_file)
                return

            for feed in feeds.get("rss_feeds", []):
                feed_name = (
                    feed.get("feed_name", "default_feed").lower().replace(" ", "_")
                )
                feed_url = feed.get("url")
                if not feed_url:
                    logger.warning(
                        "No 'url' field found for feed in JSON file: %s", json_file
                    )
                    continue

                task_id = f'fetch_{outlet_name.lower().replace(" ", "_")}_{feed_name}'
                fetch_task = FetchRSSFeedOperator(
                    task_id=task_id,
                    feed_url=feed_url,
                    es_index="rss_feeds",
                    outlet_name=outlet_name,
                    dag=dag,
                )
                logger.info("Created task with ID: %s", task_id)
                fetch_task

    except Exception as e:
        logger.error("Error processing JSON file %s: %s", json_file, e)


# Iterate over all JSON files in the config directory
config_dir = os.path.join(os.getcwd(), "config", "news_outlets")
for file_name in os.listdir(config_dir):
    if file_name.endswith(".json"):
        file_path = os.path.join(config_dir, file_name)
        logger.info("Processing JSON file: %s", file_path)
        create_rss_tasks(file_path)
