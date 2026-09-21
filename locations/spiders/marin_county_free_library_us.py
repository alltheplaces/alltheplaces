from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class MarinCountyFreeLibraryUSSpider(BiblioCommonsSpider):
    name = "marin_county_free_library_us"
    item_attributes = {"operator": "Marin County Free Library", "operator_wikidata": "Q6763710"}
    library_id = "marinlibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name", None) or ""
        if branch.startswith("Bookmobile"):
            # The bookmobile, listed at the Civic Center branch's address.
            return
        if branch == "Anne T. Kent California Room":
            # The local history collection, a room inside the Civic Center
            # branch and sharing its address and coordinates.
            return

        item["branch"] = branch
        item["name"] = "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
