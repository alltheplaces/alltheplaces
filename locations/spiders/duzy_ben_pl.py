import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class DuzyBenPLSpider(Spider):
    name = "duzy_ben_pl"
    item_attributes = {"brand": "Duży Ben", "brand_wikidata": "Q110428071"}
    start_urls = ["https://duzyben.pl/wp-content/themes/duzyben/stores/stores.json.js"]

    def parse(self, response, **kwargs):
        data = json.loads(response.text.removeprefix("var stores ="))
        for feature in data:
            item = DictParser.parse(feature)
            item["street_address"] = feature["Name"]
            item["lat"] = feature["Location"]["Latitude"]
            item["lon"] = feature["Location"]["Longitude"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(feature["OpenHours"], days=DAYS_PL)
            item["phone"] = feature["Phone"]
            item["ref"] = feature["PostID"]
            yield item
