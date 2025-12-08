import re

import scrapy
import xmltodict

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BauhausNordicsSpider(scrapy.Spider):
    name = "bauhaus_nordics"
    item_attributes = {"brand": "Bauhaus", "brand_wikidata": "Q672043"}

    start_urls = ["https://www.bauhaus.dk/rest/V1/storelocator/stores"]

    def parse(self, response):
        for store_data in xmltodict.parse(response.text)["response"]["items"]["item"]:
            store_data["street_address"] = store_data.pop("address")
            item = DictParser.parse(store_data)
            item["branch"] = item.pop("name")
            item["country"] = store_data["country_id"]
            item["phone"] = re.sub(r"\s\([A-z\s]+\)", "", store_data["phone"])
            item["website"] = "https://www.bauhaus.dk/varehus/" + store_data["link"]
            if hours_data := store_data["opening_hours"].get("items"):
                item["opening_hours"] = self.parse_hours(hours_data)
            yield item

    def parse_hours(self, hrs_list):
        oh = OpeningHours()
        for day_item in hrs_list["item"]:
            oh.add_range(day_item["weekday"].title(), day_item["opens_at"], day_item["closes_at"])
        return oh
