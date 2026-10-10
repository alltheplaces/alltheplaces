from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class OaklandPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "oakland_public_library_us"
    item_attributes = {"operator": "Oakland Public Library", "operator_wikidata": "Q1090829"}
    library_id = "oaklandlibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # The system-wide reference email, given for all but one location.
        location["branchContacts"] = [
            contact
            for contact in location.get("branchContacts") or []
            if contact.get("value") != "eanswers@oaklandlibrary.org"
        ]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch in ("Main Children's Room", "Main Library TeenZone", "Oakland History Center"):
            # Departments inside the Main Library, sharing its address.
            return

        if branch == "Main Library":
            item["name"] = "Oakland Public Library"
        elif branch.endswith(" Branch"):
            item["name"] = "{} Oakland Public Library".format(branch)
        else:
            item["name"] = branch

        if branch == "Tool Lending Library":
            # A tool library run by OPL inside the Temescal branch.
            item["located_in"] = "Temescal Branch Oakland Public Library"

        apply_category(Categories.LIBRARY, item)

        yield item
