from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GoldsmithsGBSpider(Spider):
    name = "goldsmiths_gb"
    item_attributes = {"brand": "Goldsmiths", "brand_wikidata": "Q16993095"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.thewosgroup.com/occ/v2/Goldsmiths_UK/stores?longitude=0&latitude=0&radius=100000&pageSize=10000"
        )

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["ref"] = location.pop("name")
            location["address"]["street_address"] = clean_address(
                [location["address"].get("line1"), location["address"].get("line2")]
            )
            location["phone"] = location["address"].get("phone")
            location["email"] = location["address"].get("email")

            item = DictParser.parse(location)
            item["country"] = "GB"
            item["branch"] = item.pop("name")
            item["website"] = f'https://www.goldsmiths.co.uk/store/{item["ref"]}'

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]["weekDayOpeningList"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(
                    rule["weekDay"],
                    rule["openingTime"]["formattedHour"],
                    rule["closingTime"]["formattedHour"],
                    time_format="%I:%M %p",
                )

            yield item
