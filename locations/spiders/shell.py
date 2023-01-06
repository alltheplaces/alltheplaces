import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.bp import decode_hours


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
        apply_category(Categories.FUEL_STATION, item)
        if "shop" in amenities:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        apply_yes_no("amenity:chargingstation", item, "electric_charging_other" in fuels or "shell_recharge" in fuels)
        apply_yes_no("toilets", item, "toilet" in amenities)
        apply_yes_no("atm", item, "atm" in amenities)
        apply_yes_no("car_wash", item, "carwash" in amenities)
        apply_yes_no("hgv", item, "hgv_lane" in amenities)
        apply_yes_no("wheelchair", item, "disabled_facilities" in amenities)
        apply_yes_no(Fuel.DIESEL, item, any("diesel" in f for f in fuels))
        apply_yes_no(Fuel.ADBLUE, item, any("adblue" in a for a in amenities))
        apply_yes_no(Fuel.BIODIESEL, item, "biodiesel" in fuels or "biofuel_gasoline" in fuels)
        apply_yes_no(Fuel.CNG, item, "cng" in fuels)
        apply_yes_no(Fuel.GTL_DIESEL, item, "gtl" in fuels)
        apply_yes_no(Fuel.HGV_DIESEL, item, "truck_diesel" in fuels or "hgv_lane" in amenities)
        apply_yes_no(Fuel.PROPANE, item, "auto_rv_propane" in fuels)
        apply_yes_no(Fuel.LH2, item, "hydrogen" in fuels)
        apply_yes_no(Fuel.LNG, item, "lng" in fuels)
        apply_yes_no(Fuel.LPG, item, "autogas_lpg" in fuels)
        # definition of low-octane varies by country; 92 is most common
        apply_yes_no(Fuel.OCTANE_92, item, "low_octane_gasoline" in fuels)
        # definition of mid-octane varies by country; 95 is most common
        apply_yes_no(Fuel.OCTANE_95, item, any("midgrade_gasoline" in f for f in fuels) or "unleaded_super" in fuels)
        # the US region seems to also use 'premium_gasoline' to refer to non-diesel gas products
        apply_yes_no(Fuel.OCTANE_98, item, any("98" in f for f in fuels) or "premium_gasoline" in fuels)
        apply_yes_no(Fuel.OCTANE_100, item, "super_premium_gasoline" in fuels)
        decode_hours(item, result)
        yield item
