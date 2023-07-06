from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class UnitedPetroleumAUSpider(Spider):
    name = "united_petroleum_au"
    # Note on brand: some locations are labelled as "Astron Rural"
    # in the source data, but almost all of them show on street view
    # imagery as having "United" branding. It does not appear to be
    # possible to determine whether a location is "Astron" or
    # "United" branded, but in all but seemingly < 5 cases, United
    # is almost always used.
    item_attributes = {"brand": "United Petroleum", "brand_wikidata": "Q28224393"}
    allowed_domains = ["servicestations.unitedpetroleum.com.au"]
    start_urls = ["https://servicestations.unitedpetroleum.com.au/api/find"]

    def start_requests(self):
        data = {
            "brand": [],
            "facilitiesAndServices": [],
            "foodAndDrinks": [],
            "fuelCards": [],
            "fuels": [],
            "lat": -37.8585540736312,
            "lon": 145.02824508187487,
            "range": 20000,
            "supermarketVouchers": [],
            "truckFriendly": [],
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = " ".join(
                filter(None, [location["address1"], location["address2"], location["address3"]])
            )
            item["phone"] = location["publicPhoneNumber"]
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if not location["openingHours"].get("from") or not location["openingHours"].get("to"):
                    continue
                if location["openingHours"][f"closedOn{day_name}"]:
                    continue
                if (
                    location["openingHours"][f"open24Hours{day_name}"]
                    or "24 HOURS" in location["openingHours"][day_name.lower()].upper()
                ):
                    item["opening_hours"].add_range(day_name, "00:00", "23:59")
                else:
                    open_time, close_time = (
                        location["openingHours"][day_name.lower()]
                        .upper()
                        .replace("TO", "-")
                        .replace(".", ":")
                        .replace("`", "")
                        .split("-", 2)
                    )
                    if "AM" in open_time or "AM" in close_time or "PM" in open_time or "PM" in close_time:
                        if ":" not in open_time:
                            open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
                            close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
                        item["opening_hours"].add_range(day_name, open_time.strip(), close_time.strip(), "%I:%M%p")
                    else:
                        item["opening_hours"].add_range(day_name, open_time.strip(), close_time.strip())
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.OCTANE_98, item, location["fuels"]["premium98"], False)
            apply_yes_no(Fuel.OCTANE_95, item, location["fuels"]["premiumULP"], False)
            apply_yes_no(Fuel.E10, item, location["fuels"]["plus"], False)
            apply_yes_no(Fuel.E85, item, location["fuels"]["e85"], False)
            apply_yes_no(Fuel.DIESEL, item, location["fuels"]["predis"] or location["fuels"]["diesel"], False)
            apply_yes_no(Fuel.LPG, item, location["fuels"]["lpg"], False)
            apply_yes_no(Fuel.ADBLUE, item, location["fuels"]["adblue"], False)
            apply_yes_no(Fuel.PROPANE, item, location["facilitiesAndServices"]["bbqGas"], False)
            apply_yes_no(Extras.TOILETS, item, location["facilitiesAndServices"]["toilets"], False)
            apply_yes_no(Extras.SHOWERS, item, location["facilitiesAndServices"]["showers"], False)
            apply_yes_no(Extras.ATM, item, location["facilitiesAndServices"]["atm"], False)
            apply_yes_no(Extras.CAR_WASH, item, location["facilitiesAndServices"]["carWash"], False)
            if location.get("foodAndDrinks"):
                apply_yes_no(Extras.DRIVE_THROUGH, item, location["foodAndDrinks"]["driveThru"], False)
                if location["foodAndDrinks"]["roadhouse"]:
                    apply_category(Categories.RESTAURANT, item)
                    apply_yes_no(Extras.INDOOR_SEATING, item, True)
                if location["foodAndDrinks"]["quickStop"]:
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                if location["foodAndDrinks"]["pieFace"] or location["foodAndDrinks"]["baristaCoffee"]:
                    apply_category(Categories.FAST_FOOD, item)
                    apply_yes_no(Extras.TAKEAWAY, item, True)
                    cuisine = ""
                    if location["foodAndDrinks"]["pieFace"] and location["foodAndDrinks"]["baristaCoffee"]:
                        cuisine = "pie;coffee_shop"
                    elif location["foodAndDrinks"]["pieFace"]:
                        cuisine = "pie"
                    elif location["foodAndDrinks"]["baristaCoffee"]:
                        cuisine = "coffee_shop"
                    apply_category({"cuisine": cuisine}, item)
            yield item
