from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BipaATSpider(Spider):
    name = "bipa_at"
    item_attributes = {"brand": "Bipa", "brand_wikidata": "Q864933"}
    start_urls = ["https://www.bipa.at/stores"]

    def parse(self, response: Response):
        for store in response.json():
            feature = DictParser.parse(store)
            opening_hours = OpeningHours()
            for day, range in store["storeHours"].items():
                opening_hours.add_ranges_from_string(f"{day}: {range}")
            feature["opening_hours"] = opening_hours
            yield feature
