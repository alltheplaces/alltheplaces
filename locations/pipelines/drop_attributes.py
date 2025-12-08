from scrapy import Spider

from locations.items import Feature


class DropAttributesPipeline:
    def process_item(self, item: Feature, spider: Spider):
        if not hasattr(spider, "drop_attributes"):
            return item

        for attribute in getattr(spider, "drop_attributes"):
            if attribute in item.fields:
                item.pop(attribute, None)
            else:
                item["extras"].pop(attribute, None)

        return item
