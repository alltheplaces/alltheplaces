from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CartersUSSpider(SitemapSpider, StructuredDataSpider):
    name = "carters_us"
    item_attributes = {"brand": "Carter's", "brand_wikidata": "Q5047083"}
    allowed_domains = ["www.carters.com"]
    sitemap_urls = ["https://www.carters.com/sitemap_index.xml"]
    sitemap_follow = ["store-page"]
    sitemap_rules = [(r"^https://www.carters.com/l/\w\w/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("Oshkosh "):
            item["branch"] = item.pop("name").removeprefix("Oshkosh ").removesuffix(" OshKosh")
            item["name"] = "Carter's OshKosh"
        elif item["name"].startswith("Carter’s "):
            item["branch"] = item.pop("name").removeprefix("Carter’s ").removesuffix(" Carters")
            item["name"] = "Carter's"

        oh = OpeningHours()
        for day_time in ld_data["openingHours"]:
            oh.add_ranges_from_string(day_time)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
