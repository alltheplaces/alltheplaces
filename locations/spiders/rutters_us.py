import chompjs
from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

FUEL_TYPES = {
    "Regular": Fuel.GASOLINE,
    "Unleaded 15": Fuel.E15,
    "Flex Fuel": Fuel.E85,
    "Ethanol Free": Fuel.ETHANOL_FREE,
    "Auto Diesel": Fuel.DIESEL,
    "Truck Diesel": Fuel.HGV_DIESEL,
    "DEF": Fuel.ADBLUE,
    "Off Road Diesel": Fuel.UNTAXED_DIESEL,
    "Kerosene": Fuel.KEROSENE,
}
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class RuttersUSSpider(Spider):
    name = "rutters_us"
    item_attributes = {"brand": "Rutter's", "brand_wikidata": "Q7383544", "country": "US"}
    allowed_domains = ["www.rutters.com"]
    start_urls = ["https://www.rutters.com/stores/"]

    def parse(self, response):
        stores = (chompjs.parse_js_object(response.xpath('//*[@id="rutters-map-script-js-extra"]/text()').get())).get(
            "stores"
        )
        for store in stores.values():
            store.update(store.pop("store_meta"))
            item = DictParser.parse(store)
            item["name"] = store.get("post_title")
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_CONVENIENCE, item)
            amenities = set(store.get("amenities") or [])
            for source_name, attribute in {
                "Surcharge Free ATM": Extras.ATM,
                "Free WiFi": Extras.WIFI,
                "Restrooms": Extras.TOILETS,
                "Car Wash": Extras.CAR_WASH,
                "Air Machine": Extras.COMPRESSED_AIR,
            }.items():
                apply_yes_no(attribute, item, source_name in amenities)

            yield item
