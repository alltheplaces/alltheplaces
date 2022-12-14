import scrapy

from locations.categories import Categories, Fuel, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, day_range
from locations.spiders.costacoffee_gb import yes_or_no


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
                # A fuel stattion to decode.
                result["street_address"] = result.pop("address")
                item = DictParser.parse(result)
                default = self.my_brands["BP"]
                item["brand"], item["brand_wikidata"] = self.my_brands.get(result["site_brand"], default)
                products = result["products"]
                facilities = result["facilities"]
                item["extras"] = {
                    "amenity:chargingstation": yes_or_no("electricity" in products),
                    "amenity:toilets": yes_or_no("toilet" in facilities),
                    "atm": yes_or_no("cash_point" in facilities),
                    "car_wash": yes_or_no("car_wash" in facilities),
                    "hgv": yes_or_no(any("truck" in f for f in facilities)),
                    "wheelchair": yes_or_no("disabled_facilities" in facilities),
                }
                apply_category(Categories.FUEL_STATION, item)
                if "shop" in facilities:
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                Fuel.ADBLUE.apply(item, any("ad_blue" in p for p in products))
                Fuel.DIESEL.apply(item, any("diesel" in p for p in products))
                Fuel.COLD_WEATHER_DIESEL.apply(item, "diesel_frost" in products)
                Fuel.E10.apply(item, "e10" in products)
                Fuel.E5.apply(item, "euro_95" in products or "super_e5" in products)
                Fuel.GTL_DIESEL.apply(item, any("ultimate_diesel" in p for p in products))
                Fuel.HGV_DIESEL.apply(item, "truck_diesel" in products)
                Fuel.LPG.apply(item, "lpg" in products)
                Fuel.OCTANE_100.apply(item, any("100" in p for p in products))
                Fuel.OCTANE_91.apply(item, any("premium_unlead" in p for p in products))
                Fuel.OCTANE_92.apply(item, any("92" in p for p in products))
                Fuel.OCTANE_93.apply(item, any("93" in p for p in products))
                Fuel.OCTANE_95.apply(item, "unlead" in products or any("unleaded_95" in p for p in products))
                Fuel.OCTANE_98.apply(item, "ultimate_unleaded" in products or any("98" in p for p in products))
                Fuel.UNTAXED_DIESEL.apply(item, "red_diesel" in products)
                decode_hours(item, result)
                yield item
