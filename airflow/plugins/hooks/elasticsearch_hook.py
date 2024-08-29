from elasticsearch import Elasticsearch


class ElasticsearchHook:

    def __init__(self, hosts=None):
        self.es = Elasticsearch(hosts or ["http://elasticsearch:9200"])

    def index_data(self, index, id, body):
        return self.es.index(index=index, id=id, body=body)

    def exists(self, index, id):
        return self.es.exists(index=index, id=id)
