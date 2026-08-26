from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NorautoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "norauto_fr"
    item_attributes = {"brand": "Norauto", "brand_wikidata": "Q3317698"}
    allowed_domains = ["centres.norauto.fr"]
    sitemap_urls = ["https://centres.norauto.fr/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["AutoRepair"]
    time_format = "%I:%M%p"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if name := item.pop("name", None):
            item["branch"] = name.removeprefix("Norauto ").strip() or None
        # The site's structured data exposes coordinates via non-standard top level
        # "latitude"/"longitude" properties rather than the standard "geo" property.
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
