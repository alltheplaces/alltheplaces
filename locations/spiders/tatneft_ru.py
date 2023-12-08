import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

# https://api.gs.tatneft.ru/api/v2/azs/fuel_types/
FUEL_TYPES_MAPPING = {
    2: Fuel.OCTANE_92,
    3: Fuel.OCTANE_92,
    5: Fuel.OCTANE_95,
    7: Fuel.OCTANE_98,
    9: Fuel.DIESEL,
    10: Fuel.DIESEL,
    13: Fuel.LPG,
    19: Fuel.CNG,
    20: Fuel.DIESEL,
}
# https://api.gs.tatneft.ru/api/v2/azs/features/
FEATURES_MAPPING = {
    2: Extras.COMPRESSED_AIR,
    3: Extras.FAST_FOOD,
    7: Extras.ATM,
    9: Extras.WIFI,
    10: Extras.CAR_WASH,
    15: Extras.TOILETS,
    18: Extras.VACUUM_CLEANER,
    # TODO: find tags for features like Tyre service (16) & Car Service (4)
}


class TatneftRUSpider(scrapy.Spider):
    name = "tatneft_ru"
    item_attributes = {"brand": "Татнефть", "brand_wikidata": "Q1616858"}
    allowed_domains = ["api.gs.tatneft.ru"]
    start_urls = ["https://api.gs.tatneft.ru/api/v2/azs/"]

    def parse(self, response):
        for poi in response.json()["data"]:
            item = DictParser.parse(poi)
            if photos := poi.get("photos"):
                # assume first photo is the main
                item["image"] = photos[0]
            self.parse_fuels(item, poi)
            self.parse_features(item, poi)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_fuels(self, item, poi):
        if fuels := poi.get("fuel"):
            for fuel in fuels:
                fuel_id = fuel.get("fuel_type_id")
                if tag := FUEL_TYPES_MAPPING.get(fuel_id):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/tatneft_ru/fuel/failed/{fuel_id}")

    def parse_features(self, item, poi):
        if features := poi.get("features"):
            for feature in features:
                if tag := FEATURES_MAPPING.get(feature):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/tatneft_ru/feature/failed/{feature}")
