from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ErnstingsFamilySpider(Spider):
    name = "ernstings_family"
    item_attributes = {
        "brand": "Ernsting’s family",
        "brand_wikidata": "Q1361016",
    }
    start_urls = ["https://filialen.ernstings-family.de/api/stores/nearby/51.3127114/9.4797461/10000/3000"]
    requires_proxy = "DE"

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["open_for_business"]:
                location["id"] = location.pop("storeCode")
                location["name"] = location.pop("locationName")
                location["street_address"] = ", ".join(location["addressLines"])
                location["country"] = location.pop("regionCode")
                location["phone"] = location.pop("primaryPhone")
                item = DictParser.parse(location)
                item["opening_hours"] = self.format_opening_hours(location["regularHours"]["periods"])
                item["extras"] = {"placeid": location["placeid"]}

                yield item

    def format_opening_hours(self, periods):
        hours = OpeningHours()
        for period in periods:
            hours.add_range(period["openDay"], period["openTime"], period["closeTime"])
        return hours
