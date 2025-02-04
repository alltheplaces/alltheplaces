from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class RadleyGBSpider(CrawlSpider):
    name = "radley_gb"
    item_attributes = {
        "brand": "Radley",
        "brand_wikidata": "Q7281436",
        "country": "GB",
    }
    allowed_domains = ["radley.co.uk"]
    start_urls = ["https://www.radley.co.uk/stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/stores/outlets/([-\w]+)$"),
            callback="parse",
            follow=False,
        ),
        Rule(
            LinkExtractor(allow=r"/stores/shops/([-\w]+)$"),
            callback="parse",
            follow=False,
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()

        item["website"] = response.url
        item["ref"] = response.url
        item["lat"] = response.xpath("//script/@latitude").get()
        item["lon"] = response.xpath("//script/@longitude").get()
        yield item
