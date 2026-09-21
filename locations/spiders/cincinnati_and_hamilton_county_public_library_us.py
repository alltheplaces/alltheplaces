from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class CincinnatiAndHamiltonCountyPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "cincinnati_and_hamilton_county_public_library_us"
    item_attributes = {
        "operator": "Cincinnati and Hamilton County Public Library",
        "operator_wikidata": "Q5492644",
    }
    library_id = "cincinnatilibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if not location.get("hours") and "temporary" in (location.get("hoursNote") or ""):
            # e.g. Avondale, whose listed address is a temporary site that
            # has stopped service while the branch building is renovated.
            return

        if item["name"].endswith(" Branch Library"):
            item["branch"] = item["name"].removesuffix(" Branch Library")
        apply_category(Categories.LIBRARY, item)

        yield item
