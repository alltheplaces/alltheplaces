import logging
from collections import deque
from functools import reduce
from operator import or_

import firebase_admin
from firebase_admin import credentials, firestore
from mergedeep import merge
from scrapy.statscollectors import StatsCollector

logger = logging.getLogger(__name__)


def expand_dict(d):
    def recurse_keys(keys, value):
        return {keys.pop(0): recurse_keys(keys, value) if len(keys) > 0 else value}

    return merge(*[recurse_keys(k.split("/"), v) for k, v in d.items()])


def compress_dict(d, prefix=""):
    def merge2(*dicts):
        return {
            k: reduce(lambda d, x: x.get(k, d), dicts, None)
            for k in reduce(or_, map(lambda x: x.keys(), dicts), set())
        }

    return (
        merge2(*[compress_dict(v, (f"{prefix}/{k}" if prefix != "" else k)) for k, v in d.items()])
        if isinstance(d, dict)
        else {prefix: d}
    )


class GoogleFirestoreCollector(StatsCollector):
    def __init__(self, crawler):
        super().__init__(crawler)
        self.env = None
        self.firestore_client = None

    def _document(self, spider):
        return self.firestore_client.collection(f"atp_stats_history-{self.env}").document(spider.name)

    def open_spider(self, spider):
        settings = spider.crawler.settings
        max_stored_stats = settings.getint("SPIDERMON_MAX_STORED_STATS", default=100)
        self.env = settings.get("ENV")

        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, options={"projectId": settings.get("GCP_PROJECT_ID")})
        self.firestore_client = firestore.client()

        doc = self._document(spider).get().to_dict()
        spider.stats_history = deque(
            [compress_dict(s) for s in doc["entries"]] if doc is not None else [], maxlen=max_stored_stats
        )

        logging.info("Reading stats history from Google FireStore")

    def _persist_stats(self, stats, spider):
        spider.stats_history.appendleft(self._stats)

        self._document(spider).set({"entries": [expand_dict(s) for s in spider.stats_history]})

        logging.info("Saving stats history to Google FireStore")
