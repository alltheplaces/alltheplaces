from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SanFranciscoPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "san_francisco_public_library_us"
    item_attributes = {"operator": "San Francisco Public Library", "operator_wikidata": "Q2901530"}
    library_id = "sfpl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Most branch names are published in upper case, e.g. "NOE VALLEY".
        branch = (item.pop("name") or "").title()
        if "Bookmobile" in branch:
            return

        item["branch"] = branch
        item["name"] = (
            self.item_attributes["operator"] if branch == "Main Library" else "{} Branch Library".format(branch)
        )
        if city := item.get("city"):
            item["city"] = city.rstrip(",")

        apply_category(Categories.LIBRARY, item)

        yield item
