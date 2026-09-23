from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.communico import CommunicoSpider

LOCATION_URL = "https://lacountylibrary.org/location/{}/"
# East Rancho Dominguez has no "about_url". Slug checked against lacountylibrary.org.
BRANCH_PAGES = {"2724": "east-rancho-dominguez-library"}
# Where the library files events held elsewhere or online; neither is a place.
NON_BRANCHES = {"Off-Site", "Virtual Program"}


class LaCountyLibraryUSSpider(CommunicoSpider):
    name = "la_county_library_us"
    item_attributes = {"operator": "LA County Library", "operator_wikidata": "Q5177889"}
    communico_client = "lacountylibrary"

    def pre_process_data(self, location: dict, **kwargs) -> None:
        if (location.get("line3") or "").casefold() == (location.get("locality") or "").casefold():
            # East Rancho Dominguez repeats its city as a third address line.
            location["line3"] = ""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if item["name"] in NON_BRANCHES or item["name"].endswith("Resource Center"):
            # A resource centre is a special collection housed inside a branch,
            # sharing its building, address and coordinates.
            return

        # "about_url" redirects to the canonical branch page.
        if slug := BRANCH_PAGES.get(location["id"]) or (location.get("about_url") or "").rstrip("/").rsplit("/", 1)[-1]:
            item["website"] = LOCATION_URL.format(slug)

        if not any(character.isdigit() for character in item.get("street_address") or ""):
            # El Camino Real's address line is missing its house number.
            item["street"] = item.pop("street_address")

        apply_category(Categories.LIBRARY, item)

        yield item
