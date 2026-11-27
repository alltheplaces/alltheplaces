from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WinchellsDonutHouseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "winchells_donut_house_us"
    item_attributes = {
        "brand": "Winchell's Donut House",
        "brand_wikidata": "Q8023756",
        "name": "Winchell's Donut House",
    }
    sitemap_urls = ["https://locations.winchells.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z-]+/[a-z-]+/[^/]*[a-z][^/]*/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for spec in ld_data.get("openingHoursSpecification", []):
            spec["opens"] = spec["opens"][:5]
            spec["closes"] = spec["closes"][:5]
            if spec["opens"] == spec["closes"]:
                spec["closes"] = "24:00"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = str(ld_data["branchCode"])
        apply_category(Categories.FAST_FOOD, item)
        yield item
