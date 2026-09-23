import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# e.g. "Mountain View (Randle)", "North Mason (Belfair)", where the bracketed
# part is the town the branch is named after.
LOCALITY_HINT_REGEX = re.compile(r"\s*\([^)]*\)$")
# Locations which already state what they are, e.g. "Toledo Kiosk".
SELF_DESCRIBING_NAME_REGEX = re.compile(r"\b(?:Library|Kiosk)\b")
HOUSENUMBER_REGEX = re.compile(r"(\d+\S*)\s+(.+)")


class TimberlandRegionalLibraryUSSpider(BiblioCommonsSpider):
    name = "timberland_regional_library_us"
    item_attributes = {"operator": "Timberland Regional Library", "operator_wikidata": "Q7804695"}
    library_id = "timberland"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # Some branches have the house number at the start of the street
        # rather than in "number", e.g. "110 S. Silver Street".
        address = location.get("address") or {}
        if not address.get("number") and (m := HOUSENUMBER_REGEX.fullmatch(address.get("street") or "")):
            address["number"], address["street"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = LOCALITY_HINT_REGEX.sub("", item.pop("name"))
        if branch in ("Anywhere Library", "TRL Headquarters"):
            # An outreach service delivered at other venues, and the
            # administrative building, both at the headquarters address.
            return
        if branch == "Shoalwater Bay Tribal Community Library":
            # The Shoalwater Bay Indian Tribe's own library, which cooperates
            # with Timberland for holds pickup rather than being operated by
            # them.
            return

        if SELF_DESCRIBING_NAME_REGEX.search(branch):
            item["name"] = branch
        else:
            item["branch"] = branch
            item["name"] = "{} Timberland Library".format(branch)

        if branch == "Toledo Kiosk":
            # A Timberland kiosk inside the volunteer-run Toledo Community
            # Library.
            item["located_in"] = "Toledo Community Library"

        apply_category(Categories.LIBRARY, item)

        yield item
