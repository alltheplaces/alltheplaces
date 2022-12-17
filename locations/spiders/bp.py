import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, day_range


def decode_hours(item, result):
    if "twenty_four_hour" == result.get("open_status"):
        item["opening_hours"] = "24/7"
        return
    open_hours = result.get("opening_hours")
    if len(open_hours) == 0:
        return
    oh = OpeningHours()
    for spec in open_hours:
        days = spec["days"]
        day_from = day_to = days[0]
        if len(days) == 2:
            day_to = days[1]
        for day in day_range(DAYS_EN[day_from], DAYS_EN[day_to]):
            for hours in spec["hours"]:
                oh.add_range(day, hours[0], hours[1])
    item["opening_hours"] = oh.as_opening_hours()


class BPSpider(scrapy.Spider):
    name = "bp"
    item_attributes = {"brand": "BP", "brand_wikidata": "Q152057"}
    url_template = "https://bpretaillocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D={}&sw%5B%5D={}&ne%5B%5D={}&ne%5B%5D={}"
    my_brands = {
        "BP": ("BP", "Q152057"),
        "AM": ("Amoco", "Q465952"),
        "ARAL Tankstelle": ("Aral", "Q565734"),
    }

    def start_requests(self):
        yield scrapy.Request(self.url_template.format(-90, -180, 90, 180))

    def parse(self, response):
        for result in response.json():
            if b := result.get("bounds"):
                # Bounding box for a further API call.
                yield scrapy.Request(self.url_template.format(b["sw"][0], b["sw"][1], b["ne"][0], b["ne"][1]))
            elif result.get("name"):
                # A fuel station to decode.
                result["street_address"] = result.pop("address")
                item = DictParser.parse(result)
                default = self.my_brands["BP"]
                item["brand"], item["brand_wikidata"] = self.my_brands.get(result["site_brand"], default)
                products = result["products"]
                facilities = result["facilities"]
                apply_category(Categories.FUEL_STATION, item)
                if "shop" in facilities:
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                apply_yes_no("amenity:chargingstation", item, "electricity" in products)
                apply_yes_no("amenity:toilets", item, "toilet" in facilities)
                apply_yes_no("atm", item, "cash_point" in facilities)
                apply_yes_no("car_wash", item, "car_wash" in facilities)
                apply_yes_no("hgv", item, any("truck" in f for f in facilities))
                apply_yes_no("wheelchair", item, "disabled_facilities" in facilities)
                apply_yes_no(Fuel.ADBLUE, item, any("ad_blue" in p for p in products))
                apply_yes_no(Fuel.DIESEL, item, any("diesel" in p for p in products))
                apply_yes_no(Fuel.COLD_WEATHER_DIESEL, item, "diesel_frost" in products)
                apply_yes_no(Fuel.E10, item, "e10" in products)
                apply_yes_no(Fuel.E5, item, "euro_95" in products or "super_e5" in products)
                apply_yes_no(Fuel.GTL_DIESEL, item, any("ultimate_diesel" in p for p in products))
                apply_yes_no(Fuel.HGV_DIESEL, item, "truck_diesel" in products)
                apply_yes_no(Fuel.LPG, item, "lpg" in products)
                apply_yes_no(Fuel.OCTANE_100, item, any("100" in p for p in products))
                apply_yes_no(Fuel.OCTANE_91, item, any("premium_unlead" in p for p in products))
                apply_yes_no(Fuel.OCTANE_92, item, any("92" in p for p in products))
                apply_yes_no(Fuel.OCTANE_93, item, any("93" in p for p in products))
                apply_yes_no(Fuel.OCTANE_95, item, "unlead" in products or any("unleaded_95" in p for p in products))
                apply_yes_no(Fuel.OCTANE_98, item, "ultimate_unleaded" in products or any("98" in p for p in products))
                apply_yes_no(Fuel.UNTAXED_DIESEL, item, "red_diesel" in products)
                decode_hours(item, result)
                yield item
