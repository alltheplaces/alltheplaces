from scrapy import Spider

from locations.items import Feature


class DropLogoPipeline:
    def process_item(self, item: Feature, spider: Spider):
        if image := item.get("image"):
            if isinstance(image, str):
                if "logo" in image or "favicon" in image:
                    item["image"] = None
                    spider.crawler.stats.inc_value("atp/field/image/dropped")

        return item
