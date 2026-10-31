from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class BotanicFRSpider(Spider):
    name = "botanic_fr"
    item_attributes = {"brand_wikidata": "Q2911642"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.botanic.com/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/",
            headers={"X-HTTP-Method-Override": "GET"},
            data={
                "websiteId": 100541,
                "sectionId": 100541,
                "pageId": 101275,
                "data": {
                    "currentStoreId": 0,
                    "distanceUnit": "kilometers",
                    "distance": "20000kilometers",
                    "coordinates": {"latitude": 0, "longitude": 0},
                },
                "dataSets": "coordinates,address,card,hours",
                "URLFormats": "canonical",
                "pagination": "0,1000",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["items"]:
            address = store["address"]["fields"]
            item = Feature()
            item["ref"] = store["common"]["code"]
            item["branch"] = store["common"]["title"].split("botanic® ", 1)[-1]
            item["website"] = store["common"]["URL"]["canonical"]
            item["lat"] = store["coordinates"]["latitude"]
            item["lon"] = store["coordinates"]["longitude"]
            item["street_address"] = address.get("street")
            item["postcode"] = address.get("zipCode")
            item["city"] = address.get("locality")
            item["country"] = address.get("countryCode")
            card = store["card"] or {}
            item["phone"] = card.get("phone")
            item["email"] = card.get("email")

            item["opening_hours"] = OpeningHours()
            for rule in store["hours"]["openingHours"]:
                day = DAYS[(rule["num"] - 1) % 7]
                times = [rule[period] for period in ["amBegin", "amEnd", "pmBegin", "pmEnd"] if rule.get(period)]
                if not times:
                    item["opening_hours"].set_closed(day)
                for open_time, close_time in zip(times[::2], times[1::2]):
                    item["opening_hours"].add_range(day, open_time, close_time)

            yield item
