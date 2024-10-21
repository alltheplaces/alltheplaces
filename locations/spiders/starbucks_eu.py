import scrapy

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES

# Full list of features: https://www.starbucks.co.uk/api/v2/storeFeatures/
FEATURES_MAPPING = {
    "DT": Extras.DRIVE_THROUGH,
    "GO": Extras.WIFI,
    "OS": Extras.OUTDOOR_SEATING,
    "WF": Extras.WIFI,
    "XO": PaymentMethods.APP,
}


class StarbucksEUSpider(scrapy.Spider):
    name = "starbucks_eu"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES

    def start_requests(self):
        base_url = "https://www.starbucks.co.uk/api/v2/stores/?filter[coordinates][latitude]={}&filter[coordinates][longitude]={}&filter[radius]=250"

        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv"):
            yield scrapy.Request(base_url.format(lat, lon))

    def parse(self, response):
        for poi in response.json().get("data", []):
            # move most of the attributes to the top level
            attributes = poi.pop("attributes", {})
            coordinates = poi.pop("coordinates", {})
            address = attributes.pop("address", {})
            poi = {**poi, **attributes, **coordinates, **address}
            item = DictParser.parse(poi)
            item["ref"] = poi["storeNumber"]
            item["branch"] = item.pop("name")
            self.parse_hours(item, poi)
            self.parse_features(item, poi)
            apply_category(Categories.COFFEE_SHOP, item)
            yield item

    def parse_hours(self, item: Feature, poi: dict):
        if poi.get("open24x7") is True:
            item["opening_hours"] = "24/7"
            return

        if not poi.get("openHours"):
            return

        try:
            hours = poi.get("openHours")
            oh = OpeningHours()
            for day_name, data in hours.items():
                day = DAYS_EN.get(day_name.title())
                if data.get("open") is False:
                    oh.set_closed(day)
                    continue

                open_time = data.get("openTime")
                close_time = data.get("closeTime")
                if data.get("open24Hours") is True:
                    open_time = "00:00"
                    close_time = "23:59"
                oh.add_range(day, open_time, close_time, time_format="%H:%M:%S")
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")

    def parse_features(self, item, poi):
        if features := poi.get("features", []):
            for feature in features:
                if match := FEATURES_MAPPING.get(feature.get("code")):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(
                        f"atp/{self.name}/features/fail/{feature.get('code')}/{feature.get('name')}"
                    )
