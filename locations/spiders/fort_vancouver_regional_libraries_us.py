from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class FortVancouverRegionalLibrariesUSSpider(BiblioCommonsSpider):
    name = "fort_vancouver_regional_libraries_us"
    item_attributes = {"operator": "Fort Vancouver Regional Libraries", "operator_wikidata": "Q5472215"}
    library_id = "fvrlibraries"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if "Bookmobile" in item["name"] or location["id"] == "FV-DIST":
            # Bookmobiles, and the Operations Center (administration and
            # support services).
            return

        if item.get("phone") == "+1-360-906-5000":
            # The district's central number, listed for about half of the
            # branches.
            item.pop("phone")

        apply_category(Categories.LIBRARY, item)

        yield item
