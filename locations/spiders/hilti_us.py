from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HiltiUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hilti_us"
    item_attributes = {"brand": "Hilti", "brand_wikidata": "Q1361530"}
    sitemap_urls = ["https://www.hilti.com/sitemap_stores_en_US.xml"]
    sitemap_rules = [("/stores/", "parse")]
    wanted_types = ["Store"]
    time_format = "%H:%M:%S"
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = None
        if item["name"].startswith("Distribution Center "):
            return
        else:
            item["branch"] = (
                item.pop("name")
                .removeprefix("Hilti Store ")
                .removesuffix(" (Cashless)")
                .removesuffix(" Distribution Center")
                .removesuffix(" and")
                .removesuffix(" &")
                .removesuffix(" Store")
            )

        apply_category(Categories.SHOP_POWER_TOOLS, item)

        yield item
