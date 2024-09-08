import json
import os

from elasticsearch_dsl import connections


# Configure Elasticsearch connection
def get_es_connection():
    host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    port = os.getenv("ELASTICSEARCH_PORT", "9200")
    es_url = f"http://{host}:{port}"

    return connections.create_connection(hosts=[es_url])


# Configure OpenAI connection
def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def load_prompts(file_path: str) -> dict:
    """Load prompts from a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)


def get_prompts() -> dict:
    # Load prompts from current directory
    file_path = "webserver/prompts.json"
    return load_prompts(file_path)
