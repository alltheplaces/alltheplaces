from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# The API lists these two branches surname first with the neighbourhood
# appended; their own branch pages call them "Richard J. Daley Branch" and
# "Richard M. Daley Branch".
INVERTED_BRANCH_NAMES = {
    "Daley, Richard J.-Bridgeport": "Richard J. Daley",
    "Daley, Richard M.-W Humboldt": "Richard M. Daley",
}


class ChicagoPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "chicago_public_library_us"
    item_attributes = {"operator": "Chicago Public Library", "operator_wikidata": "Q1060421"}
    library_id = "chipublib"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Harold Washington Library Center":
            item["branch"] = "Harold Washington"
            item["name"] = branch
        elif branch.endswith(" Regional"):
            item["branch"] = branch.removesuffix(" Regional")
            item["name"] = "{} Library".format(branch)
        else:
            item["branch"] = INVERTED_BRANCH_NAMES.get(branch, branch)
            item["name"] = "{} Branch Library".format(item["branch"])

        apply_category(Categories.LIBRARY, item)

        yield item
