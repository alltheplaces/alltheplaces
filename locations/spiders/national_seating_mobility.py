from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NationalSeatingMobilitySpider(SitemapSpider, StructuredDataSpider):
    name = "national_seating_mobility"
    item_attributes = {"brand": "National Seating & Mobility", "brand_wikidata": "Q116770969"}
    sitemap_urls = ["https://locations.nsm-seating.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.nsm-seating\.com/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")
        item.pop("name", None)
        apply_category(Categories.SHOP_MEDICAL_SUPPLY, item)
        yield item
