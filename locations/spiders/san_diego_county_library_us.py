from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SanDiegoCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "san_diego_county_library_us"
    item_attributes = {"operator": "San Diego County Library", "operator_wikidata": "Q7413630"}
    library_id = "sdcl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # "ᛜ" is prefixed to non-branch locations to sort them last.
        branch = item.pop("name").lstrip("ᛜ")
        if branch == "Administrative Offices" or branch.startswith("MySDCL Kiosk:"):
            # The administration office, and self-service lending machines.
            return

        item["branch"] = branch
        item["name"] = "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
