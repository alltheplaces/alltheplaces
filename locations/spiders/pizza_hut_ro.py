import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PizzaHutROSpider(scrapy.Spider):
    name = "pizza_hut_ro"
    PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.RESTAURANT.value}
    PIZZA_HUT_DELIVERY = {
        "brand": "Pizza Hut Delivery",
        "brand_wikidata": "Q191615",
        "extras": Categories.FAST_FOOD.value,
    }
    item_attributes = PIZZA_HUT
    start_urls = ["https://www.pizzahut.ro/getLocations"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location.get("coordinates").split(",")
            if "Delivery" in location["name"]:
                item.update(self.PIZZA_HUT_DELIVERY)
                timing = location.get("scheduleDelivery")
            else:
                item.update(self.PIZZA_HUT)
                timing = location.get("scheduleDineIn") or location.get("scheduleDelivery")

            item["opening_hours"] = OpeningHours()
            if timing:
                for rule in timing:
                    open_time = rule["startHour"]
                    close_time = rule["endHour"]
                    item["opening_hours"].add_range(DAYS[int(rule["weekDay"]) - 1], open_time, close_time, "%H:%M:%S")
            if services := location.get("storeServices"):
                apply_yes_no(Extras.TAKEAWAY, item, services["take_away"])
                apply_yes_no(Extras.DELIVERY, item, services["delivery"])
                apply_yes_no(Extras.INDOOR_SEATING, item, services["dine_in"])
                apply_yes_no(Extras.OUTDOOR_SEATING, item, services["outdoor_seating"])
                apply_yes_no(Extras.WIFI, item, services["wi_fi"])
            yield item
