from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_FULL, OpeningHours


class CardFactoryGBSpider(Spider):
    name = "card_factory_gb"
    item_attributes = {"brand": "Card Factory", "brand_wikidata": "Q5038192"}
    url_template = "https://www.cardfactory.co.uk/on/demandware.store/Sites-cardfactory-UK-Site/default/Stores-FindStores?showMap=true&radius=100&lat={}&long={}"

    async def start(self) -> AsyncIterator[Request]:
        for country in ["GB", "IE"]:
            for city in city_locations(country, 10000):
                yield Request(
                    self.url_template.format(city["latitude"], city["longitude"]),
                    callback=self.parse,
                    cb_kwargs=dict(country=country),
                )

    def parse(self, response, country):
        for store in response.json()["stores"]["stores"]:
            item = DictParser.parse(store)
            item["country"] = country
            item["street_address"] = store["address2"]
            item["branch"] = item.pop("name")
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if day in store["storeHoursJSON"]:
                    try:
                        item["opening_hours"].add_range(
                            day,
                            open_time=store["storeHoursJSON"][day]["start"],
                            close_time=store["storeHoursJSON"][day]["end"],
                        )
                    except:
                        self.logger.info(f"Bad format for opening hours {store['storeHoursJSON']}")
                elif day.upper() in store["storeHoursJSON"]:
                    try:
                        item["opening_hours"].add_range(
                            day,
                            open_time=store["storeHoursJSON"][day.upper()]["start"],
                            close_time=store["storeHoursJSON"][day.upper()]["end"],
                        )
                    except:
                        self.logger.info(f"Bad format for opening hours {store['storeHoursJSON']}")
            yield item
