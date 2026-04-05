from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WagamamaGBSpider(CrawlSpider, StructuredDataSpider):
    name = "wagamama_gb"
    item_attributes = {"brand": "Wagamama", "brand_wikidata": "Q503715"}
    allowed_domains = ["wagamama.com"]
    start_urls = ["https://www.wagamama.com/restaurants"]
    rules = [
        Rule(
            LinkExtractor(allow="/restaurants/", restrict_xpaths='//*[@class="_list_nzdug_20"]'),
            callback="parse_sd",
            follow=True,
        ),
        Rule(LinkExtractor(allow=r"/restaurants/[^/]+/[^/]+"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("wagamama", "")
        extract_google_position(item, response)
        yield item
