from typing import AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.item import Item


class TrackSourcesMiddleware:
    """
    Track the URLs used for each generated item,
    and overall stats per hostname.
    """

    def _process_item(self, response: Response, item: Item, spider: Spider) -> None:
        if not isinstance(item.get("extras"), dict):
            item["extras"] = {}

        if not item["extras"].get("@source_uri"):
            item["extras"]["@source_uri"] = response.url
        if not spider.crawler.stats:
            return

        try:
            spider.crawler.stats.inc_value(
                "atp/item_scraped_host_count/{}".format(urlparse(item["extras"]["@source_uri"]).netloc)
            )
        except ValueError:
            spider.logger.error("Failed to parse @source_uri: {}".format(item["extras"]["@source_uri"]))
            spider.crawler.stats.inc_value("atp/parse_error/@source_uri")

    def process_spider_output(
        self, response: Response, result: Iterable[Item | Request], spider: Spider
    ) -> Iterable[Item | Request]:
        for x in result:
            if isinstance(x, Item):
                self._process_item(response, x, spider)
            yield x

    async def process_spider_output_async(
        self, response: Response, result: AsyncIterator[Item | Request], spider: Spider
    ) -> AsyncIterator[Item | Request]:
        async for x in result:
            if isinstance(x, Item):
                self._process_item(response, x, spider)
            yield x
