import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AllsaintsSpider(CrawlSpider, StructuredDataSpider):
    name = "allsaints"
    item_attributes = {"brand": "AllSaints", "brand_wikidata": "Q4728473"}
    start_urls = ["https://www.allsaints.com/storesresult/"]
    rules = [Rule(LinkExtractor(allow=r"/stores/(?:[\w-]+/[\w-]+/)?[\w-]+$"), callback="parse")]

    wanted_types = ["Store"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": BROWSER_DEFAULT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "upgrade-insecure-requests": "1",
        },
    }
    search_for_email = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.xpath("//@data-store-id").get()
        item["branch"] = re.sub(r"^all+\s?saints\s+", "", item.pop("name"), flags=re.IGNORECASE)
        if not item["image"]:
            item["image"] = None
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
