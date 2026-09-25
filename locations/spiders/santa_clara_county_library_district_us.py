from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SantaClaraCountyLibraryDistrictUSSpider(BiblioCommonsSpider):
    name = "santa_clara_county_library_district_us"
    item_attributes = {"operator": "Santa Clara County Library District", "operator_wikidata": "Q181372"}
    library_id = "sccl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # "Bookmobile" and "Services & Support Center" (administration).
        if location.get("id") in {"BK", "HQ"}:
            return

        # Names are already full, e.g. "Campbell Library", "Woodland Branch Library".
        branch = item["name"].removesuffix(" Library").removesuffix(" Branch")
        if branch != item["name"]:
            item["branch"] = branch
        apply_category(Categories.LIBRARY, item)

        yield item
