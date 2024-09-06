import os

from elasticsearch_dsl import connections


# Configure Elasticsearch connection
def get_es_connection():
    host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    port = os.getenv("ELASTICSEARCH_PORT", "9200")
    es_url = f"http://{host}:{port}"

    return connections.create_connection(hosts=[es_url])
