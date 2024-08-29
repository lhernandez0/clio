import logging

from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ElasticsearchHook:

    def __init__(self, hosts=None):
        self.es = Elasticsearch(hosts or ["http://elasticsearch:9200"])
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized ElasticsearchHook with hosts: %s", hosts)

    def index_data(self, index, id, body):
        try:
            response = self.es.index(index=index, id=id, body=body)
            self.logger.info("Indexed document with ID: %s into index: %s", id, index)
            return response
        except Exception as e:
            self.logger.error(
                "Failed to index document with ID: %s into index: %s. Error: %s",
                id,
                index,
                e,
            )
            raise

    def exists(self, index, id):
        try:
            exists = self.es.exists(index=index, id=id)
            self.logger.info(
                "Checked existence of document with ID: %s in index: %s. Exists: %s",
                id,
                index,
                exists,
            )
            return exists
        except Exception as e:
            self.logger.error(
                "Failed to check existence of document with ID: %s in index: %s. Error: %s",
                id,
                index,
                e,
            )
            raise
