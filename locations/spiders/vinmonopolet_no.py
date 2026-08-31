from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_NO, OpeningHours, day_range, sanitise_day


class VinmonopoletNOSpider(Spider):
    name = "vinmonopolet_no"
    item_attributes = {"brand": "Vinmonopolet", "brand_wikidata": "Q1740534"}
    allowed_domains = ["www.vinmonopolet.no"]
    start_urls = ["https://www.vinmonopolet.no/vmpws/v2/vmp/stores?fields=FULL&pageSize=1000"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location.get("displayName")
            item["addr_full"] = location["address"].get("formattedAddress")
            item["website"] = "https://www.vinmonopolet.no/butikk/" + item["ref"]

            oh = OpeningHours()
            try:
                for day_hours in location.get("openingHours").get("weekDayOpeningList"):
                    day = day_hours["day"]["formattedValue"]
                    if "–" in day:
                        start_day, end_day = day.split("–")
                        start_day = sanitise_day(start_day, DAYS_NO)
                        end_day = sanitise_day(end_day, DAYS_NO)
                    else:
                        start_day = end_day = sanitise_day(day, DAYS_NO)
                    open_time = day_hours["hours"]["openingHour"]
                    close_time = day_hours["hours"]["closingHour"]
                    oh.add_days_range(day_range(start_day, end_day), open_time, close_time)
                item["opening_hours"] = oh
            except:
                pass
            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
