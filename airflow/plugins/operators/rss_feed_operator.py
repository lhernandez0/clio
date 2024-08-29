import feedparser
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from hooks.elasticsearch_hook import ElasticsearchHook


class FetchRSSFeedOperator(BaseOperator):

    @apply_defaults
    def __init__(self, feed_url, es_index, outlet_name, *args, **kwargs):
        super(FetchRSSFeedOperator, self).__init__(*args, **kwargs)
        self.feed_url = feed_url
        self.es_index = es_index
        self.outlet_name = outlet_name
        self.es = ElasticsearchHook()

    def execute(self, context):
        parsed_feed = feedparser.parse(self.feed_url)
        for entry in parsed_feed.entries:
            # Check if the article already exists in Elasticsearch
            if not self.es.exists(index=self.es_index, id=entry.link):
                doc = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "summary": entry.summary,
                    "source": self.outlet_name,
                }
                # Index the new article
                self.es.index_data(index=self.es_index, id=entry.link, body=doc)
