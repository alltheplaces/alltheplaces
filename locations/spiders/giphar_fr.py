import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GipharFRSpider(SitemapSpider, StructuredDataSpider):
    name = "giphar_fr"
    item_attributes = {"brand": "Giphar", "brand_wikidata": "Q3107556"}
    allowed_domains = ["pharmacies.giphar.fr"]
    sitemap_urls = ["https://pharmacies.giphar.fr/sitemap.xml"]
    sitemap_rules = [(r"/[^/]+/[^/]+/[^/]+/[^/]+-(\d+)$", "parse_sd")]
    wanted_types = ["MedicalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if name := item.get("name"):
            # "PHARMACIE DU LEVANT - ABBEVILLE" -> "Pharmacie du Levant"
            name = name.rsplit(" - ", 1)[0].title()
            item["name"] = re.sub(r"(?<=\w )((?:De[sl]?|Du|L[ae]s?)\b|[LD]')", lambda m: m.group().lower(), name)
        item["ref"] = response.url.rsplit("-", 1)[-1]
        # socials in the LD are the brand accounts, not per-store
        item.pop("twitter", None)
        item.pop("facebook", None)
        apply_category(Categories.PHARMACY, item)
        yield item
