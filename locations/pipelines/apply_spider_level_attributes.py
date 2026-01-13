from scrapy.crawler import Crawler


class ApplySpiderLevelAttributesPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item):
        if not hasattr(self.crawler.spider, "item_attributes"):
            return item

        item_attributes = self.crawler.spider.item_attributes

        for key, value in item_attributes.items():  # ty: ignore [unresolved-attribute]
            if key == "extras":
                extras = item.get("extras", {})
                for k, v in value.items():
                    if extras.get(k) is None:
                        extras[k] = v
                item["extras"] = extras
            else:
                if item.get(key) is None:
                    item[key] = value

        return item
