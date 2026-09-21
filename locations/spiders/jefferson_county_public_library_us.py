import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

LOCKER_NAME_REGEX = re.compile(r"\bholds lockers?\b", re.IGNORECASE)
# e.g. "Arvada Library (Closed for Redesign)", where the closure is already
# recorded in the opening hours.
CLOSURE_SUFFIX_REGEX = re.compile(r"\s*\(Closed[^)]*\)$", re.IGNORECASE)
# The system-wide "Ask Us" number, listed as the contact for every location.
SYSTEM_PHONE = "+1-303-235-5275"


class JeffersonCountyPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "jefferson_county_public_library_us"
    item_attributes = {"operator": "Jefferson County Public Library", "operator_wikidata": "Q69470275"}
    library_id = "jeffcolibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        location["branchContacts"] = [
            contact
            for contact in location.get("branchContacts") or []
            if (contact.get("globalValue") or contact.get("value")) != SYSTEM_PHONE
        ]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("id") == "BK":
            # The bookmobile, listed at the depot it is garaged at.
            return

        if LOCKER_NAME_REGEX.search(item["name"]):
            apply_category(Categories.PARCEL_LOCKER, item)
        else:
            # Every library is named "<Branch> Library" already.
            item["name"] = CLOSURE_SUFFIX_REGEX.sub("", item["name"])
            apply_category(Categories.LIBRARY, item)

        yield item
