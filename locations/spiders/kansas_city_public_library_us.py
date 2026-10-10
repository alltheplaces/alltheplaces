from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class KansasCityPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "kansas_city_public_library_us"
    item_attributes = {"operator": "Kansas City Public Library", "operator_wikidata": "Q6364835"}
    library_id = "kclibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("id") == "KC-MBL01":  # Bookmobile
            return

        branch = item.pop("name", None) or ""
        item["branch"] = branch.removesuffix(" Branch").removesuffix(" Library")
        item["name"] = branch if branch.endswith("Library") else "{} Library".format(branch)

        apply_category(Categories.LIBRARY, item)

        yield item
