from typing import Any

import scrapy
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class KruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    start_urls = [
        "https://www.kruidvat.be/api/v2/kvb/stores?lang=nl_BE&radius=100000&pageSize=10000&fields=FULL",
        "https://www.kruidvat.nl/api/v2/kvn/stores?lang=nl&radius=100000&pageSize=10000&fields=FULL",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//stores"):
            item = Feature()
            item["name"] = store.xpath(".//displayName/text()").get()
            item["state"] = store.xpath(".//province/text()").get()
            item["postcode"] = store.xpath(".//postalCode/text()").get()
            item["street"] = store.xpath(".//line1/text()").get()
            item["lat"] = store.xpath(".//latitude/text()").get()
            item["lon"] = store.xpath(".//longitude/text()").get()
            item["addr_full"] = store.xpath(".//formattedAddress/text()").get()
            item["opening_hours"] = OpeningHours()
            for day_time in store.xpath(".//weekDayOpeningList"):
                open_time = day_time.xpath("./openingTime/formattedHour/text()").get()
                close_time = day_time.xpath("./closingTime/formattedHour/text()").get()
                day = day_time.xpath(".//shortenedWeekDay/text()").get()
                if day:
                    item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

            if ".nl" in response.url:
                item["ref"] = item["website"] = "https://www.kruidvat.nl/" + store.xpath(".//url/text()").get()
            else:
                item["ref"] = item["website"] = "https://www.kruidvat.be/" + store.xpath(".//url/text()").get()
            yield item
