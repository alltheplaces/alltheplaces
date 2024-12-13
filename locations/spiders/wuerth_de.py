import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class WuerthDESpider(scrapy.Spider):
    name = "wuerth_de"
    item_attributes = {"brand": "Würth", "brand_wikidata": "Q679750"}
    start_urls = ["https://www.wuerth.de/web/de/awkg/niederlassungen/branches_json_v2.json"]

    def parse(self, response, **kwargs):
        for location in response.json():
            rename = {
                "address": "street_address",
                "branch": "name",
                "branchnumber": "ref",
                "imageUrl": "image",
                "location": "city",
                "nlDetailUrl": "website",
            }
            for old, new in rename.items():
                location[new] = location.pop(old)
            location["website"] = location["website"].strip()
            item = DictParser.parse(location)
            item["image"] = location["image"]
            item["opening_hours"] = self.parse_opening_hours(location["openings"])
            yield item

    def parse_opening_hours(self, openings):
        hours = OpeningHours()
        for day, interval_list in openings.items():
            if "openings" in interval_list:
                for interval in interval_list["openings"]:
                    hours.add_range(day, interval["open"], interval["close"], time_format="%H.%M")
        return hours
