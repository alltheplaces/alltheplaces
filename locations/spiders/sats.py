from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SatsSpider(SitemapSpider, StructuredDataSpider):
    name = "sats"
    item_attributes = {"brand": "Sats", "brand_wikidata": "Q4411496"}
    sitemap_urls = [
        "https://www.sats.se/sitemap.xml",
        "https://www.sats.no/sitemap.xml",
        "https://www.sats.dk/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/gym/[^/]+/[^/]+$", "parse_sd"),
        (r"/treningssenter/[^/]+$", "parse_sd"),
        (r"/traeningscenter/[^/]+$", "parse_sd"),
    ]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").strip()
        item["website"] = response.url
        if geo := ld_data.get("location", {}).get("geo"):
            item["lat"] = geo.get("latitude")
            item["lon"] = geo.get("longitude")
        apply_category(Categories.GYM, item)
        yield item
