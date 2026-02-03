from scrapy.crawler import Crawler

from locations.items import Feature


class DropLogoPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:
        if image := item.get("image"):
            if isinstance(image, str):
                if "logo" in image or "favicon" in image:
                    item["image"] = None
                    if self.crawler.stats:
                        self.crawler.stats.inc_value("atp/field/image/dropped")

        return item
