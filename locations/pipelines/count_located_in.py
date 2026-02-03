from scrapy.crawler import Crawler

from locations.items import Feature


class CountLocatedInPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if self.crawler.stats:
            if located_in := item.get("located_in"):
                self.crawler.stats.inc_value(f"atp/located_in/{located_in}")
            if wikidata := item.get("located_in_wikidata"):
                self.crawler.stats.inc_value(
                    f"atp/located_in_wikidata/{wikidata}"
                )
        return item
