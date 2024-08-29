import logging

import feedparser
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from hooks.elasticsearch_hook import ElasticsearchHook

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FetchRSSFeedOperator(BaseOperator):

    @apply_defaults
    def __init__(self, feed_url, es_index, outlet_name, *args, **kwargs):
        super(FetchRSSFeedOperator, self).__init__(*args, **kwargs)
        self.feed_url = feed_url
        self.es_index = es_index
        self.outlet_name = outlet_name
        self.es = ElasticsearchHook()
        self.logger = logging.getLogger(__name__)

    def execute(self, context):
        self.logger.info("Starting to process feed: %s", self.feed_url)
        try:
            parsed_feed = feedparser.parse(self.feed_url)
            for entry in parsed_feed.entries:
                if not self.es.exists(index=self.es_index, id=entry.link):
                    doc = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published,
                        "summary": entry.summary,
                        "source": self.outlet_name,
                    }
                    self.es.index_data(index=self.es_index, id=entry.link, body=doc)
                    self.logger.info("Indexed new document with ID: %s", entry.link)
                else:
                    self.logger.info("Document with ID %s already exists", entry.link)
        except Exception as e:
            self.logger.error("Error processing feed %s: %s", self.feed_url, e)
            raise
