from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.elfsight import ElfsightSpider


class YwcaUSSpider(ElfsightSpider):
    name = "ywca_us"
    item_attributes = {"brand": "YWCA", "brand_wikidata": "Q17022739"}
    host = "core.service.elfsight.com"
    api_key = "9a21c171-1a02-4a3e-bbc8-e5fb34782244"

    def pre_process_data(self, feature: dict) -> None:
        # Coordinates are "lat lon" (space separated), not the "lat, lon" the base
        # class expects.
        if coordinates := feature.get("coordinates"):
            feature["coordinates"] = coordinates.replace(" ", ", ", 1)
        super().pre_process_data(feature)

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        # Addresses are published as a single free-text line with inconsistent
        # formatting (missing commas, zip codes without leading zeros, PO boxes),
        # so it isn't reliably splittable into street/city/state/postcode. DictParser
        # already maps the "addr" key (set by the base class) to addr_full.
        if site := location.get("infoSite"):
            if not site.startswith(("http://", "https://")):
                site = f"https://{site}"
            if "facebook.com" in site:
                item["facebook"] = site
            else:
                item["website"] = site
        apply_category(Categories.COMMUNITY_CENTRE, item)
        yield item
