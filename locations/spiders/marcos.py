import json
import time

import chompjs
from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours


def minutes_to_time(minutes: int):
    return time.gmtime(minutes * 60)


class MarcosSpider(Spider):
    name = "marcos"
    item_attributes = {
        "brand": "Marco's Pizza",
        "brand_wikidata": "Q6757382",
    }
    # First get country info
    start_urls = [
        "https://momspublicstorage.blob.core.windows.net/content/moms/online/brand-data/online-brand-data-LPHP3Y.json"
    ]

    def parse(self, response):
        countries = {country["CountryID"]: country for country in response.json()["CONTs"]}
        # Then fetch locations
        yield Request(
            "https://order.marcos.com/brand/?sk=LPHP3Y/locations",
            callback=self.parse_locations,
            cb_kwargs={"countries": countries},
        )

    def parse_locations(self, response, countries):
        locations = json.loads(
            chompjs.parse_js_object(response.xpath('//script[contains(text(), "let Temp = ")]/text()').get())[
                "BrandLocations"
            ]
        )
        for location in locations:
            item = DictParser.parse(location)
            item["country"] = countries[location["countryId"]]["IsoCode"]
            item["ref"] = location["storeKey"]
            item["phone"] = (
                None
                if item["phone"] == "1111111111"
                else countries[location["countryId"]]["CountryCode"] + item["phone"]
            )
            item["extras"]["website:orders"] = f"{location['OnlineOrderingURL']}?id={location['storeKey']}"

            oh = OpeningHours()
            for day in location["Hours"]:
                oh.add_range(
                    DAYS_FROM_SUNDAY[day["WeekDayNo"]],
                    minutes_to_time(day["OpenDayMinute"]),
                    minutes_to_time(day["CloseDayMinute"]),
                )
            item["opening_hours"] = oh

            yield item
