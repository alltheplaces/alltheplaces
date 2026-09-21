import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

BOOK_LOCKER_NAME_REGEX = re.compile(r"\bbook lockers?\b", re.IGNORECASE)


class CentralArkansasLibrarySystemUSSpider(BiblioCommonsSpider):
    name = "central_arkansas_library_system_us"
    item_attributes = {"operator": "Central Arkansas Library System", "operator_wikidata": "Q5060351"}
    library_id = "cals"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name", None) or ""

        if branch in ("Arkansas Museum of Fine Arts", "UAMS Hold Pickup Location"):
            # Partner venues listed in the catalogue for holds pickup: an
            # independent museum and the university's own medical library.
            # Neither is run by CALS and the API gives no coordinates for them.
            return

        if BOOK_LOCKER_NAME_REGEX.search(branch):
            item["name"] = branch
            apply_category(Categories.PARCEL_LOCKER, item)
        else:
            # Every branch is named "<Branch> Library" already.
            item["branch"] = branch.removesuffix(" Library")
            item["name"] = branch
            apply_category(Categories.LIBRARY, item)

        yield item
