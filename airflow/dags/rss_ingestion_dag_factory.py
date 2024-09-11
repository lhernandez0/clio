import json
import logging
import os
from datetime import datetime, timedelta

from operators.rss_feed_operator import FetchRSSFeedOperator
from utils.utils import generate_dag_list

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

logger = logging.getLogger(__name__)


# Function to clean feed name
def clean_feed_name(name):
    # Remove non-alphanumeric characters and replace spaces with underscores
    cleaned_name = "".join(char for char in name if char.isalnum() or char == " ")
    return cleaned_name.replace(" ", "_").lower()


# Function to create a DAG dynamically
def create_dag(dag_id, json_file):
    logger.info(f"Creating DAG from JSON file: {json_file}")
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=f"A DAG to ingest RSS feeds from {json_file}",
        schedule_interval=timedelta(minutes=60),  # Runs every hour
        catchup=False,
    )

    with open(json_file, "r") as f:
        feeds = json.load(f)
        outlet_name = feeds.get("name")
        if not outlet_name:
            logger.warning("No 'name' field found in JSON file: %s", json_file)
            return None

        previous_task = None
        for feed in feeds.get("rss_feeds", []):
            feed_name = clean_feed_name(feed.get("feed_name", "default_feed"))
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

            # Set task dependencies to ensure sequential execution
            if previous_task:
                previous_task >> fetch_task

            previous_task = fetch_task

    return dag


# Iterate over all JSON files in the config directory and create a DAG for each
config_dir = os.path.join(os.getcwd(), "config", "news_outlets")
dag_list = generate_dag_list(config_dir)

# Create and register each DAG
for dag_id, file_path in dag_list:
    globals()[dag_id] = create_dag(dag_id, file_path)
