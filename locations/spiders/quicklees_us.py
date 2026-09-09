from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class QuickleesUSSpider(SitemapSpider, StructuredDataSpider):
    name = "quicklees_us"
    item_attributes = {"name": "Quicklee's", "brand": "Quicklee's"}
    sitemap_urls = ["https://quicklees.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = ld_data.get("@id") or response.url
        apply_category(Categories.SHOP_CONVENIENCE, item)
        apply_category(Categories.FUEL_STATION, item)
        yield item
