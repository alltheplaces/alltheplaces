from scrapy.crawler import Crawler

from locations.items import Feature


class CountOperatorsPipeline:
    crawler: Crawler

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if operator := item.get("operator"):
            self.crawler.stats.inc_value(f"atp/operator/{operator}")
        if wikidata := item.get("operator_wikidata"):
            self.crawler.stats.inc_value(f"atp/operator_wikidata/{wikidata}")
        return item
