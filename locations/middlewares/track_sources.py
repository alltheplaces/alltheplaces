from urllib.parse import urlparse

from scrapy.item import Item


class TrackSourcesMiddleware:
    """
    Track the URLs used for each generated item,
    and overall stats per hostname.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler

    def _process_item(self, response, item, spider):
        if isinstance(item, Item):
            if "source:url" not in item["extras"]:
                item["extras"]["source:url"] = response.url

            self.crawler.stats.inc_value(
                "atp/item_scraped_host_count/{}".format(urlparse(item["extras"]["source:url"]).netloc)
            )

    def process_spider_output(self, response, result, spider):
        for item in result or []:
            self._process_item(response, item, spider)
            yield item

    async def process_spider_output_async(self, response, result, spider):
        async for item in result or []:
            self._process_item(response, item, spider)
            yield item
