import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

HOUSENUMBER_REGEX = re.compile(r"(\d+\S*)\s+(.+)")


class JohnsonCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "johnson_county_library_us"
    item_attributes = {"operator": "Johnson County Library", "operator_wikidata": "Q69476104"}
    library_id = "jocolibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        address = location.get("address") or {}
        if not (address.get("number") or "").strip():
            # The Merriam Plaza branch has no "number", with the house
            # number at the start of "street".
            if m := HOUSENUMBER_REGEX.fullmatch((address.get("street") or "").strip()):
                address["number"], address["street"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Every location is named "<Branch> Library" already.
        apply_category(Categories.LIBRARY, item)
        yield item
