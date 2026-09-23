from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class LasVegasClarkCountyLibraryDistrictUSSpider(BiblioCommonsSpider):
    name = "las_vegas_clark_county_library_district_us"
    item_attributes = {
        "operator": "Las Vegas-Clark County Library District",
        "operator_wikidata": "Q6492678",
    }
    library_id = "lvccld"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if (item.get("name") or "").startswith("The Library at "):
            # An unstaffed book vending machine inside a hospital or a
            # shopping mall, sharing the district's information line.
            return

        # Every branch is named "<Branch> Library" already.
        apply_category(Categories.LIBRARY, item)

        yield item
