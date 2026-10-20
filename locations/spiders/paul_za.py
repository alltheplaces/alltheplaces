from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class PaulZASpider(SitemapSpider, StructuredDataSpider):
    name = "paul_za"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.paulsa.co.za/sitemap.xml"]
    sitemap_rules = [(r"/restaurants-[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = (item.pop("name") or "").removeprefix("PAUL").strip()
        item.pop("image", None)
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
