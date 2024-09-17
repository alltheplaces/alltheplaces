from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class PepZMSpider(Spider):
    name = "pep_zm"
    item_attributes = {"brand": "Pep", "brand_wikidata": "Q7166182"}
    start_urls = ["https://www.pep.co.zm/api/stores.json"]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)

            item["branch"] = location["title"]
            item.pop("name")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                item["opening_hours"].add_range(
                    day, location[day.lower() + "_open"], location[day.lower() + "_close"], time_format="%H:%M:%S"
                )

            yield item
