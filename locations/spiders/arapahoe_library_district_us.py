from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class ArapahoeLibraryDistrictUSSpider(BiblioCommonsSpider):
    name = "arapahoe_library_district_us"
    item_attributes = {"operator": "Arapahoe Library District", "operator_wikidata": "Q69470148"}
    library_id = "arapahoelibraries"
    # Every location lists the district's single number, (303) 542-7279.
    drop_attributes = {"phone"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # Also listed: cafes and a makerspace inside branches, mobile library
        # services, and The Space (meeting and coworking space).
        if not item["name"].endswith(" Library"):
            return

        item["branch"] = item["name"].removesuffix(" Library")
        apply_category(Categories.LIBRARY, item)

        yield item
