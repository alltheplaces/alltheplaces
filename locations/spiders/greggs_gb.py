from datetime import datetime

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GreggsGBSpider(Spider):
    name = "greggs_gb"
    item_attributes = {"brand": "Greggs", "brand_wikidata": "Q3403981"}
    start_urls = ["https://production-digital.greggs.co.uk/api/v1.0/shops"]

    def parse(self, response):
        for store in response.json():
            store["address"]["street_address"] = clean_address(
                [
                    store["address"].pop("houseNumberOrName"),
                    store["address"].pop("streetName"),
                ]
            )
            item = DictParser.parse(store["address"])
            item["phone"] = store["address"]["phoneNumber"]
            item["ref"] = store["shopCode"]
            item["website"] = f'https://www.greggs.co.uk/shop-finder?shop-code={store["shopCode"]}'
            item["opening_hours"] = self.decode_hours(store)
            yield item

    @staticmethod
    def decode_hours(store):
        oh = OpeningHours()
        for r in store["tradingPeriods"]:
            # Each day has a record like:
            # {'openingTime': '2022-08-30T06:00:00Z', 'closingTime': '2022-08-30T18:00:00Z'}
            # Do not believe their Zulu time modifier, it is local time.
            oh.add_range(
                DAYS[datetime.fromisoformat(r["openingTime"][0:10]).weekday()],
                r["openingTime"][-9:-4],
                r["closingTime"][-9:-4],
            )
        return oh.as_opening_hours()
