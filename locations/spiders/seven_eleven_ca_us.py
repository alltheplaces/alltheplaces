import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.speedway_us import SpeedwayUSSpider

FUEL_TYPES_MAPPING = {
    "DEF": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "E85": Fuel.E85,
    "Kerosene": Fuel.KEROSENE,
    "Kersonse": Fuel.KEROSENE,
    "Mid-grade": Fuel.OCTANE_89,
    "Mid-Grade": Fuel.OCTANE_89,
    "Regular": Fuel.OCTANE_87,
    "Premium": Fuel.OCTANE_91,
}

STRIPES = {"brand": "Stripes", "brand_wikidata": "Q7624135"}


# SitemapSpider no longer works properly for US, getting identified as a bot and served with a page without data
class SevenElevenCAUSSpider(Spider):
    name = "seven_eleven_ca_us"
    start_urls = [
        "https://www.7-eleven.com/locations/tx/frisco/11065-fm-720-33117"  # Get access token from any store page
    ]
    api = "https://api.7-eleven.com/v4/stores"
    token = ""
    offset = 0
    page_size = 500

    def next_request(self) -> JsonRequest:
        return JsonRequest(
            url=f"{self.api}?offset={self.offset}&limit={self.page_size}",
            headers={"Authorization": f"Bearer {self.token}"},
            callback=self.parse_stores,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:  # parse token
        self.token = re.search(r"access_token\\\":\\\"(.+?)\\\"", response.text).group(1)
        yield self.next_request()

    def parse_stores(self, response: Response, **kwargs: Any):
        for location in response.json()["results"]:
            item = DictParser.parse(location)
            item["name"] = None
            item["street_address"] = item.pop("addr_full")
            item["website"] = location.get("seo_web_url")
            item["extras"]["ref:google:place_id"] = location.get("google_place_id")

            apply_yes_no(Extras.ATM, item, "ATM" in location.get("features_display", []))
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in location.get("features_display", []))
            apply_yes_no(Extras.WIFI, item, "Wi-Fi" in location.get("features_display", []))

            brand = location.get("brand_info") or {}
            shop = item.deepcopy()
            shop["ref"] = "{}_SHOP".format(shop["ref"])
            if brand.get("title") == "Stripes":
                shop.update(STRIPES)
            elif brand.get("title") == "7-Eleven":
                shop.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
            elif location.get("name") == "Speedway Store":
                shop.update(SpeedwayUSSpider.item_attributes)
            else:
                shop.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)

            apply_category(Categories.SHOP_CONVENIENCE, shop)

            yield shop

            if "Fuel" in location.get("features_display", []):
                if location["fuel_brand"] == 1:
                    item.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
                elif location["fuel_brand"] == 10002:
                    pass  # Conoco/Phillips 66/76
                elif location["fuel_brand"] == 10035:
                    item.update(SpeedwayUSSpider.item_attributes)
                elif location["fuel_brand"] == 10068:
                    pass  # Mainly Exxon but some Mobil
                else:
                    pass  # Mainly Sunoco

                apply_category(Categories.FUEL_STATION, item)
                self.parse_fuel_types(item, location)

                yield item

        if len(response.json()["results"]) == self.page_size:
            self.offset += self.page_size
            yield self.next_request()

    def parse_fuel_types(self, item, store):
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in store.get("features_display", []))
        apply_yes_no(Fuel.PROPANE, item, "Propane" in store.get("features_display", []))
        if fuel_data := store.get("fuel_data", {}):
            if grades := fuel_data.get("grades", []):
                for grade in grades:
                    fuel_name = grade.get("name")
                    if tag := FUEL_TYPES_MAPPING.get(fuel_name):
                        apply_yes_no(tag, item, True)
                    else:
                        # self.logger.warning(f"Unknown fuel type: {fuel_name}")
                        self.crawler.stats.inc_value(f"atp/7_11/fuel/failed/{fuel_name}")
