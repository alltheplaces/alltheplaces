from scrapy import Spider

from locations.items import Feature


class DropLogoPipeline:
    def process_item(self, item: Feature, spider: Spider):
        if image := item.get("image"):
            if isinstance(image, str):
                if "logo" in image:
                    item["image"] = None

        return item
