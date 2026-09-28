import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SlumberlandFurnitureUSSpider(SitemapSpider, StructuredDataSpider):
    name = "slumberland_furniture_us"
    item_attributes = {"brand_wikidata": "Q7542307"}
    sitemap_urls = ["https://stores.slumberland.com/sitemap.xml"]
    sitemap_rules = [(r"^https://stores\.slumberland\.com/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # The site's own JSON-LD does not include a "geo" property on the
        # "Store" object, but publishes the same store's coordinates in a
        # separate "VerifiableCredential" JSON-LD block on the same page.
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue
            if geo := data.get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")
                break

        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
