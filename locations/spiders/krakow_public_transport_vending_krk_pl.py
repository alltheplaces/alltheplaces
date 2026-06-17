import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KrakowPublicTransportVendingKrkPLSpider(JSONBlobSpider):
    name = "krakow_public_transport_vending_krk_pl"
    item_attributes = {"brand": "KKM", "brand_wikidata": "Q57515549"}
    start_urls = ["https://services.mpk.amistad.pl/mpk/pointsOfSale"]

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        # Drop dummy records like "PN" that have no coordinates
        if not item.get("lat") or not item.get("lon"):
            return

        clean_name = item.pop("name", "").replace(", obsługiwany przez Zarząd Transportu Publicznego", "").strip()
        item["extras"]["location_description"] = clean_name

        if street_match := re.search(r"(?:ul\.|al\.|[Pp]l\.|Trasa)\s+[^,\(]+", clean_name):
            item["street_address"] = street_match.group(0).strip()

        if opening_hours_raw := location.get("openingHours"):
            if opening_hours_raw == "Całą dobę":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(opening_hours_raw, DAYS_PL)

        if "[POP]" in clean_name:
            apply_category(Categories.SHOP_TICKET, item)
            item["extras"]["ticket"] = "public_transport"
            item["nsi_id"] = "N/A"
        else:
            item["extras"]["payment:cash"] = "yes" if location.get("isSupportCash") else "no"
            item["extras"]["payment:cards"] = "yes"

        yield item
