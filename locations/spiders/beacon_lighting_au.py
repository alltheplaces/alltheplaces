from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BeaconLightingAUSpider(SitemapSpider, StructuredDataSpider):
    name = "beacon_lighting_au"
    item_attributes = {"brand": "Beacon Lighting", "brand_wikidata": "Q109626941"}
    allowed_domains = ["www.beaconlighting.com.au"]
    sitemap_urls = ["https://www.beaconlighting.com.au/sitemap-stores.xml"]
    sitemap_rules = [(r"/storelocator/(.+)$", "parse_sd")]
    search_for_facebook = False  # Brand level page linked from every store page.

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # Some stores are published with a closing time earlier than the
        # opening time, which would otherwise be read as an overnight range.
        rules = ld_data.get("openingHoursSpecification") or []
        if isinstance(rules, dict):
            rules = [rules]
        ld_data["openingHoursSpecification"] = [
            rule for rule in rules if isinstance(rule, dict) and rule.get("closes", "") > rule.get("opens", "")
        ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Beacon Lighting ")
        apply_category(Categories.SHOP_LIGHTING, item)
        yield item
