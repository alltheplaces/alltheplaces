from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class MuskegonAreaDistrictLibraryUSSpider(BiblioCommonsSpider):
    name = "muskegon_area_district_library_us"
    item_attributes = {"operator": "Muskegon Area District Library", "operator_wikidata": "Q69480039"}
    library_id = "muskegonadl"
    # Email contacts are staff members, e.g. a district manager shared by
    # several branches.
    drop_attributes = {"email"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("id") == "UM":
            # Administration offices
            return

        # e.g. "Dalton Branch"; the "Library for the Visually & Physically
        # Disabled" is already a full name.
        if item["name"].endswith(" Branch"):
            item["branch"] = item["name"].removesuffix(" Branch")
            item["name"] = "{} Library".format(item["name"])

        apply_category(Categories.LIBRARY, item)

        yield item
