import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CircleKSpider(Spider):
    name = "circle_k"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    allowed_domains = ["www.circlek.com"]
    start_urls = ["https://www.circlek.com/stores_master.php?lat=0&lng=0&page=0"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0})

    def parse(self, response):
        if response.json()["count"] == 0:
            # crawl completed
            return

        for location_id, location in response.json()["stores"].items():
            item = DictParser.parse(location)
            item["ref"] = location_id
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.circlek.com" + item["website"]
            services = [service["name"] for service in location["services"]]
            apply_yes_no(Extras.ATM, item, "atm" in services or "EU_ATM" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "EU_LOUNGE" in services)
            apply_yes_no(Extras.TOILETS, item, "public_restrooms" in services or "EU_TOILETS_BOTH" in services)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "EU_BABY_CHANGING" in services)
            apply_yes_no(Extras.SHOWERS, item, "EU_SHOWER" in services)
            apply_yes_no(Extras.WIFI, item, "EU_WIFI" in services)
            apply_yes_no(
                Extras.CAR_WASH,
                item,
                "car_wash" in services
                or "car_wash_cleanfreak" in services
                or "rainstorm_car_wash" in services
                or "EU_CARWASH" in services
                or "EU_CARWASH_JETWASH" in services,
            )
            apply_yes_no(Fuel.DIESEL, item, "diesel" in services)
            apply_yes_no(Fuel.HGV_DIESEL, item, "EU_TRUCKDIESEL_NETWORK" in services)
            apply_yes_no(Fuel.ADBLUE, item, "EU_ADBLUE_SERVICE" in services)
            if (
                "gas" in services
                or "EU_GAS" in services
                or "diesel" in services
                or "EU_TRUCKDIESEL_NETWORK" in services
            ):
                apply_category(Categories.FUEL_STATION, item)
            else:
                # default category
                apply_category(Categories.SHOP_CONVENIENCE, item)
            if "ev_charger" in services or "EU_HIGH_SPEED_CHARGER" in services:
                apply_category(Categories.CHARGING_STATION, item)
            yield item

        if response.json()["count"] < 10:
            # crawl completed
            return

        next_page = response.meta["page"] + 1
        next_url = re.sub(r"\d+$", str(next_page), response.url)
        yield JsonRequest(url=next_url, meta={"page": next_page})
