from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SnoIsleLibrariesUSSpider(BiblioCommonsSpider):
    name = "sno_isle_libraries_us"
    item_attributes = {"operator": "Sno-Isle Libraries", "operator_wikidata": "Q7547864"}
    library_id = "sno-isle"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if item["name"] == "Library On Wheels":
            return
        if "Locker" in item["name"]:
            apply_category(Categories.PARCEL_LOCKER, item)
        else:
            # e.g. "Lakewood/Smokey Pt. Library", signed "Lakewood/Smokey Point Library"
            item["name"] = item["name"].replace(" Pt. ", " Point ")
            apply_category(Categories.LIBRARY, item)

        yield item
