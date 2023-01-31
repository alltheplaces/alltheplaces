from datetime import datetime

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DenmansGBSpider(Spider):
    name = "denmans_gb"
    item_attributes = {"brand": "Denmans", "brand_wikidata": "Q1"}
    # Seems to return all stores regardless of lat long as long as it's in the UK?
    start_urls = ["https://www.denmans.co.uk/den/store-finder/findNearbyStores?latitude=51&longitude=-0"]

    def parse(self, response):
        for store in response.json()["results"]:
            store["address"]["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        store["address"].pop("line1"),
                        store["address"].pop("line2"),
                        store["address"].pop("line3"),
                    ],
                )
            )
            item = DictParser.parse(store["address"])
            item["phone"] = store["address"]["phone"]
            item["name"] = store["displayName"]
            item["ref"] = store["name"]
            #https://www.denmans.co.uk/den/Bradley-Stoke-Bristol/store/1AR
            item[
                "website"
            ] = f'https://www.denmans.co.uk/den/{store["address"]["town"].replace(" ", "-")}/store/{store["name"]}'
            item["opening_hours"] = self.decode_hours(store)
            yield item

    @staticmethod
    def decode_hours(store):
        oh = OpeningHours()
        for r in store["openingHours"]["rexelWeekDayOpeningList"]:
            oh.add_range(
                r["weekDay"],
                r["openingTime"]["formattedHour"],
                r["closingTime"]["formattedHour"],
            )
        return oh.as_opening_hours()
