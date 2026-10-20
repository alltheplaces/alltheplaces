from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SaintPaulPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "saint_paul_public_library_us"
    item_attributes = {"operator": "Saint Paul Public Library", "operator_wikidata": "Q69480731"}
    library_id = "sppl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Mobile Library":
            return

        if "Library" in branch:
            # e.g. "George Latimer Central Library", "Rondo Community Library
            # at the Hallie Q. Brown Community Center"
            item["name"] = branch.split(" at the ", 1)[0]
        else:
            item["branch"] = branch
            item["name"] = "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
