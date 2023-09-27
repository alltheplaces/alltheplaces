import json

import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

FUEL_TYPES_MAPPING = {
    "DEF": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "Mid-grade": Fuel.OCTANE_89,
    "Regular": Fuel.OCTANE_87,
    "Premium": Fuel.OCTANE_91,
}

FEATURES_MAPPING = {
    "ATM": Extras.ATM,
    "Delivery": Extras.DELIVERY,
    "Diesel": Fuel.DIESEL,
    "Hot Foods": Extras.FAST_FOOD,
    "Propane": Fuel.PROPANE,
}


class SevenElevenUSSpider(scrapy.spiders.SitemapSpider):
    name = "seven_eleven_us"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    allowed_domains = ["7-eleven.com"]
    sitemap_urls = ["https://www.7-eleven.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response):
        for ld in response.xpath('//script[@type="application/json"]//text()').getall():
            ld_obj = json.loads(ld, strict=False)
            store = DictParser.get_nested_key(ld_obj, "locations")
            if not store:
                continue
            current_store = DictParser.get_nested_key(store, "currentStore")
            current_store["location"] = store.get("localStoreLatLon")
            current_store["street_address"] = current_store.pop("address")
            item = DictParser.parse(current_store)
            item["website"] = item["ref"] = response.url

            if "Fuel" in current_store.get("featuresDisplay", []):
                apply_category(Categories.FUEL_STATION, item)
                self.parse_fuel_types(item, current_store)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            self.parse_features(item, current_store)

            yield item

    def parse_fuel_types(self, item, store):
        if fuel_data := store.get("fuelData", {}):
            if grades := fuel_data.get("grades", []):
                for grade in grades:
                    fuel_name = grade.get("name")
                    if tag := FUEL_TYPES_MAPPING.get(fuel_name):
                        apply_yes_no(tag, item, True)
                    else:
                        # self.logger.warning(f"Unknown fuel type: {fuel_name}")
                        self.crawler.stats.inc_value(f"atp/7_11/fuel/failed/{fuel_name}")

    def parse_features(self, item, store):
        if features := store.get("featuresDisplay", []):
            for feature in features:
                if tag := FEATURES_MAPPING.get(feature):
                    apply_yes_no(tag, item, True)
                else:
                    # self.logger.warning(f"Unknown feature: {feature}")
                    self.crawler.stats.inc_value(f"atp/7_11/feature/failed/{feature}")
