from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FeuVertFRSpider(SitemapSpider, StructuredDataSpider):
    name = "feu_vert_fr"
    item_attributes = {"brand": "Feu Vert", "brand_wikidata": "Q3070922"}
    allowed_domains = ["www.feuvert.fr"]
    sitemap_urls = ["https://www.feuvert.fr/sitemap/centres-auto.xml"]
    sitemap_rules = [(r"/centres-auto/[^/]+/[^/]+/\d+\.html$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # Coordinates are top-level "latitude"/"longitude" fields on the
        # AutoRepair object rather than nested under "geo", which
        # LinkedDataParser does not pick up automatically.
        if lat := ld_data.get("latitude"):
            item["lat"] = lat
        if lon := ld_data.get("longitude"):
            item["lon"] = lon

        item.pop("image", None)  # Same generic illustration on every store, not a real photo

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
