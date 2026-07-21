from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class ReweDESpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "rewe_de"
    item_attributes = {"name": "Rewe", "brand": "Rewe", "brand_wikidata": "Q16968817"}
    allowed_domains = ["www.rewe.de"]
    sitemap_urls = ["https://www.rewe.de/sitemaps/sitemap-maerkte.xml"]
    sitemap_rules = [(r"/marktseite/[^/]+/(\d+)/[^/]+/$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000}

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        if opening_hours := ld_data.get("openingHours"):
            ld_data["openingHours"] = [rule.replace(" Uhr", "") for rule in opening_hours]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = None
        if item.get("street_address"):
            item["street_address"] = item["street_address"].removesuffix(" null")
        item.pop("image", None)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
