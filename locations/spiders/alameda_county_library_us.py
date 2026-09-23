from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class AlamedaCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "alameda_county_library_us"
    item_attributes = {"operator": "Alameda County Library", "operator_wikidata": "Q4705862"}
    library_id = "aclibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name", None) or ""
        if branch == "Mobile Library":
            # The bookmobile, which has no address and no fixed stop.
            return
        if branch == "Fremont":
            # The system's main library, signed and mapped as "Fremont Main".
            branch = "Fremont Main"
        elif branch == "Cherryland":
            item["located_in"] = "Cherryland Community Center"

        item["branch"] = branch
        item["name"] = "{} Library".format(branch)

        apply_category(Categories.LIBRARY, item)

        yield item
