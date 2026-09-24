from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class CentralRappahannockRegionalLibraryUSSpider(BiblioCommonsSpider):
    name = "central_rappahannock_regional_library_us"
    item_attributes = {
        "operator": "Central Rappahannock Regional Library",
        "operator_wikidata": "Q28230499",
    }
    library_id = "librarypoint"
    # Branches list either the system-wide number or one shared by the three
    # Westmoreland County branches.
    drop_attributes = {"phone"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if not branch.endswith(" Branch"):
            # Access Services (a department in Howell Branch), IdeaSpace (a
            # makerspace) and "Satellite Location"s open a few hours a week in
            # community centres.
            return

        item["branch"] = branch.removesuffix(" Branch")
        item["name"] = "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
