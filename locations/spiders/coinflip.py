from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CoinflipSpider(CrawlSpider, StructuredDataSpider):
    name = "coinflip"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    start_urls = ["https://locations.coinflip.tech/"]

    rules = [
        Rule(LinkExtractor(allow=r"/\w+$", restrict_xpaths="//main//ul")),
        Rule(LinkExtractor(allow=r"/\w+/[a-z-]+$", restrict_xpaths="//main//ul")),
        Rule(LinkExtractor(allow=r"/\w+/[a-z-]+/[a-z-]+$", restrict_xpaths="//main//ul")),
        Rule(
            LinkExtractor(
                allow=r"/\w+/[a-z-]+/[a-z-]+/[a-z-0-9]+$",
            ),
            callback="parse_sd",
        ),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUESTS": 1}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if name := item.get("name"):
            item["branch"] = name.removeprefix("CoinFlip Bitcoin ATM - ").strip() or None
        item["name"] = None
        item["phone"] = None
        item["email"] = None
        item["twitter"] = None
        item["facebook"] = None
        apply_category(Categories.ATM, item)
        apply_yes_no("currency:XBT", item, True)
        yield item
