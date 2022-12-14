import scrapy

from locations.categories import Categories, Fuel, apply_category
from locations.dict_parser import DictParser
from locations.spiders.bp import decode_hours
from locations.spiders.costacoffee_gb import yes_or_no


class ShellSpider(scrapy.Spider):
    name = "shell"
    item_attributes = {"brand": "Shell", "brand_wikidata": "Q110716465"}
    url_template = "https://shellgsllocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D={}&sw%5B%5D={}&ne%5B%5D={}&ne%5B%5D={}"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.5

    def start_requests(self):
        yield scrapy.Request(self.url_template.format(-90, -180, 90, 180))

    def parse(self, response):
        for item in response.json():
            if b := item.get("bounds"):
                # Result is an array of bounding boxes.
                yield scrapy.Request(self.url_template.format(b["sw"][0], b["sw"][1], b["ne"][0], b["ne"][1]))
            elif item.get("name"):
                # Result is an array of station listings.
                station_url = f"https://shellgsllocator.geoapp.me/api/v1/locations/{item['id']}"
                yield scrapy.Request(station_url, callback=self.parse_station)

    def parse_station(self, response):
        result = response.json()
        if result["inactive"]:
            return
        result["street_address"] = result.pop("address")
        item = DictParser.parse(result)
        item["website"] = result["website_url"]
        # Definitions extracted from https://shellgsllocator.geoapp.me/config/published/retail/prod/en_US.json?format=json
        amenities = result["amenities"]
        fuels = result["fuels"]
        item["extras"] = {
            "amenity:chargingstation": yes_or_no("electric_charging_other" in fuels or "shell_recharge" in fuels),
            "toilets": yes_or_no("toilet" in amenities),
            "atm": yes_or_no("atm" in amenities),
            "car_wash": yes_or_no("carwash" in amenities),
            "hgv": yes_or_no("hgv_lane" in amenities),
            "wheelchair": yes_or_no("disabled_facilities" in amenities),
        }
        apply_category(Categories.FUEL_STATION, item)
        if "shop" in amenities:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        Fuel.DIESEL.apply(item, any("diesel" in f for f in fuels))
        Fuel.ADBLUE.apply(item, any("adblue" in a for a in amenities))
        Fuel.BIODIESEL.apply(item, "biodiesel" in fuels or "biofuel_gasoline" in fuels)
        Fuel.CNG.apply(item, "cng" in fuels)
        Fuel.GTL_DIESEL.apply(item, "gtl" in fuels)
        Fuel.HGV_DIESEL.apply(item, "truck_diesel" in fuels or "hgv_lane" in amenities)
        Fuel.PROPANE.apply(item, "auto_rv_propane" in fuels)
        Fuel.LH2.apply(item, "hydrogen" in fuels)
        Fuel.LNG.apply(item, "lng" in fuels)
        Fuel.LPG.apply(item, "autogas_lpg" in fuels)
        # definition of low-octane varies by country; 92 is most common
        Fuel.OCTANE_92.apply(item, "low_octane_gasoline" in fuels)
        # definition of mid-octane varies by country; 95 is most common
        Fuel.OCTANE_95.apply(item, any("midgrade_gasoline" in f for f in fuels) or "unleaded_super" in fuels)
        # the US region seems to also use 'premium_gasoline' to refer to non-diesel gas products
        Fuel.OCTANE_98.apply(item, any("98" in f for f in fuels) or "premium_gasoline" in fuels)
        Fuel.OCTANE_100.apply(item, "super_premium_gasoline" in fuels)
        decode_hours(item, result)
        yield item
