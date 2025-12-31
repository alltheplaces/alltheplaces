from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TtbbankTHSpider(Spider):
    name = "ttbbank_th"
    item_attributes = {"brand": "ธนาคารทหารไทย", "brand_wikidata": "Q1527826"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for key in ["location_branch", "location_atm"]:
            yield JsonRequest(
                url="https://www.ttbbank.com/api/location",
                data={"moduleKey": key},
                cb_kwargs={"key": key},
            )

    def parse(self, response, **kwargs):
        for location in response.json().get("body").get("data"):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            item["phone"] = location.get("additional_phones")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if times := location.get("{}_hours".format(day.lower())):
                    start_time, end_time = times.replace(".", ":").split("-")
                    item["opening_hours"].add_range(day, start_time.strip(), end_time.strip())

            if kwargs["key"] == "location_branch":
                item["ref"] = str(location.get("id")) + "- branch"
                apply_category(Categories.BANK, item)
            else:
                item["ref"] = str(location.get("id")) + "- atm"
                apply_category(Categories.ATM, item)

            yield item
