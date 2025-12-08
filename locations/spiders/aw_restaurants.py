from locations.categories import Extras, apply_yes_no
from locations.storefinders.stat import StatSpider


class AwRestaurantsSpider(StatSpider):
    name = "aw_restaurants"
    item_attributes = {"brand": "A&W", "brand_wikidata": "Q277641"}
    start_urls = [
        "https://awrestaurants.com/stat/api/locations/search?limit=20000&fields=servicetags_drive_thru%2Cservicetags_outdoor_seating%2Cservicetags_breakfast%2Cservicetags_drive_in"
    ]

    def post_process_item(self, item, response, store):
        item["name"] = None
        apply_yes_no(Extras.DRIVE_THROUGH, item, store["displayFields"]["servicetags_drive_thru"])
        apply_yes_no(Extras.OUTDOOR_SEATING, item, store["displayFields"]["servicetags_outdoor_seating"])
        apply_yes_no(Extras.BREAKFAST, item, store["displayFields"]["servicetags_breakfast"])
        apply_yes_no("drive_in", item, store["displayFields"]["servicetags_drive_in"])
        yield item
