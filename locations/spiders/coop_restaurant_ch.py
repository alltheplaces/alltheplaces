from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CoopRestaurantCHSpider(JSONBlobSpider):
    name = "coop_restaurant_ch"
    item_attributes = {
        "brand": "Coop Restaurant",
        "brand_wikidata": "Q432564",
    }
    start_urls = [
        "https://www.coop-restaurant.ch/bin/coop/restaurantfinder.json?currentPage=0&language=de&latitude=46.8&longitude=8.2&onlyOpen=false&openingHoursDays=7&pageSize=1000"
    ]
    locations_key = "locations"

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("vstId")
        feature["name"] = feature.pop("namePublic")
        feature["country"] = "CH"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["opening_hours"] = self.parse_hours(feature.get("openingHoursOfTheWeek", []))

        name = item.pop("name")
        if "Take it" in name:
            apply_category(Categories.FAST_FOOD, item)
            item["branch"] = name.removeprefix("Coop Take it ")
            item["name"] = "Coop Take it"
        elif "Ca'Puccini" in name:
            apply_category(Categories.CAFE, item)
            item["branch"] = name.removeprefix("Coop Ca'Puccini ")
            item["name"] = "Coop Ca'Puccini"
        elif "Ristorante" in name:
            apply_category(Categories.RESTAURANT, item)
            item["branch"] = name.removeprefix("Coop Ristorante ")
            item["name"] = "Coop Ristorante"
        elif "Bistro" in name:
            apply_category(Categories.RESTAURANT, item)
            item["branch"] = name.removeprefix("Coop Bistro ")
            item["name"] = "Coop Bistro"
        else:
            apply_category(Categories.RESTAURANT, item)
            item["branch"] = name.removeprefix("Coop Restaurant ")
            item["name"] = "Coop Restaurant"

        yield item

    @staticmethod
    def parse_hours(hours_data: list) -> OpeningHours:
        oh = OpeningHours()
        for day_info in hours_data:
            day = DAYS_DE.get(day_info.get("day", ""))
            hours = day_info.get("hours", [])
            if not day or not hours:
                continue
            if hours[0] == "geschlossen":
                oh.set_closed(day)
            else:
                for time_range in hours:
                    if " - " in time_range:
                        open_time, close_time = time_range.split(" - ")
                        oh.add_range(day, open_time, close_time)
        return oh
