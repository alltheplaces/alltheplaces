import scrapy

from locations.categories import Categories, apply_category
from locations.country_utils import CountryUtils
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsQStoreSpider(scrapy.Spider):
    name = "mcdonalds_qstore"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.com.au", "mcdonalds.co.nz", "mcdonalds.eg"]
    start_urls = (
        "https://mcdonalds.com.au/data/store",
        "https://mcdonalds.co.nz/data/store",
        "https://mcdonalds.eg/Stotes",
    )

    def __init__(self):
        self.country_utils = CountryUtils()

    @staticmethod
    def store_hours(rules: []) -> OpeningHours:
        oh = OpeningHours()
        for day, start_time, end_time in rules:
            day = sanitise_day(day)
            if not day:
                continue
            if start_time == "9999" or end_time == "9999":
                continue
            if end_time == "2400":
                end_time = "2359"
            if start_time and end_time:
                try:
                    oh.add_range(day, start_time, end_time, time_format="%H%M")
                except:
                    pass
        return oh

    def parse(self, response):
        cc = self.country_utils.country_code_from_url(response.url)

        for data in response.json():
            properties = {
                "city": data["store_suburb"],
                "ref": data["store_code"],
                "street_address": data["store_address"],
                "phone": data.get("store_phone"),
                "state": data["store_state"],
                "postcode": data.get("store_postcode"),
                "name": data["title"],
                "geolocation": data.get("lat_long"),
            }
            item = DictParser.parse(properties)
            item["country"] = cc

            # The alternative way of providing the location.
            coords = data.get("store_geocode")
            if coords and "," in coords:
                item["lat"] = coords.split(",")[1]
                item["lon"] = coords.split(",")[0]

            item["opening_hours"] = self.store_hours(data.get("store_trading_hour", []))

            apply_category(Categories.FAST_FOOD, item)

            yield item
