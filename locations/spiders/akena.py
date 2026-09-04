from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

BLOCKED_PHONE = "800031500"


class AkenaSpider(SitemapSpider, StructuredDataSpider):
    name = "akena"
    item_attributes = {"brand": "Akena", "brand_wikidata": "Q107089744"}
    sitemap_urls = ["https://www.akena.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.akena\.com/agences/[^/]+/?$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        phone = item.get("phone")
        clean_phone = "".join(c for c in str(phone) if c.isdigit()) if phone else ""

        if BLOCKED_PHONE in clean_phone:
            self.logger.info(f"Dropping generic phone number for: {item.get('name')} - {response.url}")
            item["phone"] = None

        apply_category(Categories.CRAFT_CARPENTER, item)
        yield item
