from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.communico import CommunicoSpider

BRANCH_URL = "https://cuyahogalibrary.org/branches/{}"
# Locations which are not library branches.
NON_BRANCH_LOCATIONS = {
    "300",  # "Administration Building": the system's offices, next door to the Parma-Snow branch.
    "2669",  # "Virtual": online events rather than a place.
}


class CuyahogaCountyPublicLibraryUSSpider(CommunicoSpider):
    name = "cuyahoga_county_public_library_us"
    item_attributes = {"operator": "Cuyahoga County Public Library", "operator_wikidata": "Q5197076"}
    communico_client = "cuyahoga"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        if not location.get("locality"):
            # The city is written as a second address line and "locality" left empty.
            location["locality"] = location.get("line2") or ""
            location["line2"] = ""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location["id"] in NON_BRANCH_LOCATIONS:
            return

        # No location carries an "about_url". Slugs checked against cuyahogalibrary.org/branches.
        item["website"] = BRANCH_URL.format(item["name"].removesuffix(" Branch").lower().replace(" ", "-"))

        apply_category(Categories.LIBRARY, item)

        yield item
