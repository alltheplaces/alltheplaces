from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class OmahaPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "omaha_public_library_us"
    item_attributes = {"operator": "Omaha Public Library", "operator_wikidata": "Q17108193"}
    library_id = "omaha"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Central Library":
            # Signed and mapped as "Omaha Central Library", the 2026 replacement
            # for the demolished W. Dale Clark Library.
            item["name"] = "Omaha Central Library"
        else:
            item["name"] = branch if "Library" in branch else "{} Library".format(branch)
        item["branch"] = branch.removesuffix(" Branch").removesuffix(" Library")

        apply_category(Categories.LIBRARY, item)

        yield item
