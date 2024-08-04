import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PolitixAUSpider(Spider):
    name = "politix_au"
    item_attributes = {"brand": "Politix", "brand_wikidata": "Q126166036"}
    start_urls = [
        "https://www.politix.com.au/on/demandware.store/Sites-politix_au-Site/en_AU/PolitixStores-GetAllStores?countryCode=AU"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            # MYER/DAVID_JONES also appear
            if (
                location["storeType"]["value"] == "POLITIX_STORES"
                or location["storeType"]["value"] == "FACTORY_OUTLETS"
            ):
                item = DictParser.parse(location)
                hours_string = re.sub(
                    r"\s+", " ", location["storeHours"].replace("</p>", "").replace("<p>", "")
                ).strip()
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)
                if " (" in item["name"]:
                    item["name"] = item["name"].split(" (")[0]
                yield item
