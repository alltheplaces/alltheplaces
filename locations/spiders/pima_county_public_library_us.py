from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class PimaCountyPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "pima_county_public_library_us"
    item_attributes = {"operator": "Pima County Public Library", "operator_wikidata": "Q7194577"}
    library_id = "pima"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # "Infoline" is the system-wide information line, not a branch number.
        location["branchContacts"] = [
            contact for contact in location.get("branchContacts") or [] if contact.get("label") != "Infoline"
        ]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Every location is named "<Branch> Library" already.
        apply_category(Categories.LIBRARY, item)
        yield item
