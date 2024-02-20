import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES

FUEL_TYPES_MAPPING = {
    "DEF": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "Mid-Grade": Fuel.OCTANE_89,
    "Regular": Fuel.OCTANE_87,
    "Premium": Fuel.OCTANE_91,
}

FEATURES_MAPPING = {
    "ATM": Extras.ATM,
    "Car Wash": Extras.CAR_WASH,
    "Delivery": Extras.DELIVERY,
    "Diesel": Fuel.DIESEL,
    "Hot Foods": Extras.FAST_FOOD,
    "Propane": Fuel.PROPANE,
    "Wi-Fi": Extras.WIFI,
}


# SitemapSpider no longer works properly for US, getting identified as a bot and served with a page without data
class SevenElevenCAUSSpider(scrapy.Spider):
    name = "seven_eleven_ca_us"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.7-eleven.com/locations/wv/st-albans/301-w-main-st-35914"  # Get access token from any store page
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

    def parse(self, response):  # parse token
        token = re.search(r"access_token\\\":\\\"(.+?)\\\"", response.text).group(1)
        self.token = token
        yield self.next_request()

    def parse_stores(self, response):
        for store in response.json()["results"]:
            store["street-address"] = store.pop("address", "")
            item = DictParser.parse(store)
            item["website"] = store.get("seo_web_url")

            if "Fuel" in store.get("features_display", []):
                apply_category(Categories.FUEL_STATION, item)
                self.parse_fuel_types(item, store)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            self.parse_features(item, store)
            yield item

        if len(response.json()["results"]) == self.page_size:
            self.offset += self.page_size
            yield self.next_request()

    def parse_fuel_types(self, item, store):
        if fuel_data := store.get("fuel_data", {}):
            if grades := fuel_data.get("grades", []):
                for grade in grades:
                    fuel_name = grade.get("name")
                    if tag := FUEL_TYPES_MAPPING.get(fuel_name):
                        apply_yes_no(tag, item, True)
                    else:
                        # self.logger.warning(f"Unknown fuel type: {fuel_name}")
                        self.crawler.stats.inc_value(f"atp/7_11/fuel/failed/{fuel_name}")

    def parse_features(self, item, store):
        if features := store.get("features_display", []):
            for feature in features:
                if tag := FEATURES_MAPPING.get(feature):
                    apply_yes_no(tag, item, True)
                else:
                    # self.logger.warning(f"Unknown feature: {feature}")
                    self.crawler.stats.inc_value(f"atp/7_11/feature/failed/{feature}")
