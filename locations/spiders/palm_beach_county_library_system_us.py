import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

HOUSENUMBER_REGEX = re.compile(r"(\d+\S*)\s+(.+)")
STATE_ZIP_REGEX = re.compile(r"([A-Z]{2})\s+(\d{5})")


class PalmBeachCountyLibrarySystemUSSpider(BiblioCommonsSpider):
    name = "palm_beach_county_library_system_us"
    item_attributes = {"operator": "Palm Beach County Library System", "operator_wikidata": "Q7127985"}
    library_id = "pbclibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        address = location.get("address") or {}
        if m := STATE_ZIP_REGEX.fullmatch((address.get("state") or "").strip()):
            # The Greenacres branch has "FL 33467" in "state" and no "zip".
            address["state"], address["zip"] = m.group(1), address.get("zip") or m.group(2)
        if not (address.get("number") or "").strip():
            # The Canyon branch has its house number at the start of "street".
            if m := HOUSENUMBER_REGEX.fullmatch((address.get("street") or "").strip()):
                address["number"], address["street"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Bookmobile" or branch.startswith("Library to Go"):
            # A mobile library, and a self-service kiosk inside a recreation
            # centre: neither is a library branch.
            return

        # e.g. "Loula V. York Branch - Pahokee": the town is already in "city".
        item["branch"] = branch.split(" - ", 1)[0]
        item["name"] = item["branch"] if "Library" in item["branch"] else "{} Library".format(item["branch"])

        apply_category(Categories.LIBRARY, item)

        yield item
