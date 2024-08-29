import json
import os
from datetime import datetime, timedelta

from operators.rss_feed_operator import FetchRSSFeedOperator

from airflow import DAG

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


# Function to create tasks dynamically
def create_rss_tasks(json_file):
    with open(json_file, "r") as f:
        feeds = json.load(f)
        for feed in feeds.get("rss_feeds", []):
            task_id = f'fetch_{feeds.get("name").lower().replace(" ", "_")}_{feed["feed_name"].lower().replace(" ", "_")}'

            fetch_task = FetchRSSFeedOperator(
                task_id=task_id,
                feed_url=feed["url"],
                es_index="rss_feeds",
                outlet_name=feeds.get("name"),
                dag=dag,
            )
            fetch_task


# Iterate over all JSON files in the config directory
config_dir = os.path.join(os.getcwd(), "config", "news_outlets")
for file_name in os.listdir(config_dir):
    if file_name.endswith(".json"):
        create_rss_tasks(os.path.join(config_dir, file_name))
