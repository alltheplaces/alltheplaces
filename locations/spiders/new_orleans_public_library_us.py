from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.communico import CommunicoSpider

# Locations which are not library branches.
NON_BRANCH_LOCATIONS = {
    "2432",  # "Virtual Events": online events rather than a place.
    "3155",  # "In the Community": outreach held at other venues.
    "3529",  # "REACH Center": a coworking space and art gallery.
    "3927",  # "Desire / Florida Satellite Location": a book vending machine in a city multi-service center.
    "4571",  # "City Archives & Special Collections": a department inside the Main Library.
}


class NewOrleansPublicLibraryUSSpider(CommunicoSpider):
    name = "new_orleans_public_library_us"
    item_attributes = {"operator": "New Orleans Public Library", "operator_wikidata": "Q7010768"}
    communico_client = "neworleans"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location["id"] in NON_BRANCH_LOCATIONS:
            return

        apply_category(Categories.LIBRARY, item)

        yield item
