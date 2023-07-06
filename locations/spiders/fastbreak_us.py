from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class FastbreakUSSpider(StoreRocketSpider):
    name = "fastbreak_us"
    item_attributes = {"brand": "Fastbreak", "brand_wikidata": "Q116731804"}
    storerocket_id = "WwzpABj4dD"
    base_url = "https://www.myfastbreak.com/locations"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day, times in location["hours"].items():
            day = sanitise_day(day)
            if day and times:
                start_time, end_time = times.split("-")
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
