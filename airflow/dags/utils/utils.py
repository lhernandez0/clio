import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_dag_list(config_dir):
    dag_ids = []
    for file_name in os.listdir(config_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(config_dir, file_name)
            logger.info("Processing JSON file: %s", file_path)
            dag_id = f"{file_name.replace('.json', '')}_rss_ingestion_dag"
            dag_ids.append((dag_id, file_path))
    return dag_ids
