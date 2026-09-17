import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.bibliocommons import BiblioCommonsSpider

LOCKER_NAME_REGEX = re.compile(r"\blockers?\b", re.IGNORECASE)


class KingCountyLibrarySystemUSSpider(BiblioCommonsSpider):
    name = "king_county_library_system_us"
    item_attributes = {"operator": "King County Library System", "operator_wikidata": "Q6411390"}
    library_id = "kcls"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if LOCKER_NAME_REGEX.search(item["name"]):
            apply_category(Categories.PARCEL_LOCKER, item)
        elif branch := item.pop("name", None):
            if branch.startswith("Administrative Office"):
                # Administration building, not a library branch.
                return

            # e.g. "Kent Closed. Holds Pickup at Kent Panther Lake."
            # (temporarily closed for renovation)
            branch = branch.split(" Closed.", 1)[0]
            item["name"] = branch if "Library" in branch else "{} Library".format(branch)
            apply_category(Categories.LIBRARY, item)

        yield item
