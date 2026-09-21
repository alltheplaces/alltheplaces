from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

SYSTEM_PHONE = "+1-314-241-2288"


class StLouisPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "st_louis_public_library_us"
    item_attributes = {"operator": "St. Louis Public Library", "operator_wikidata": "Q7589673"}
    library_id = "slpl"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # Every location lists the same system-wide number rather than a
        # branch line.
        location["branchContacts"] = [
            contact for contact in location.get("branchContacts") or [] if contact.get("globalValue") != SYSTEM_PHONE
        ]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name", None) or ""
        if branch == "Central":
            # The Central Library building is signed with the system name.
            item["branch"] = "Central Library"
            item["name"] = "St. Louis Public Library"
        else:
            item["branch"] = branch.removesuffix(" Library")
            item["name"] = branch

        apply_category(Categories.LIBRARY, item)

        yield item
