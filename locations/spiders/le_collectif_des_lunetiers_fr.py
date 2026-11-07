from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class LeCollectifDesLunetiersFRSpider(Spider):
    name = "le_collectif_des_lunetiers_fr"
    # NSI still lists this Wikidata item under the former Vision Plus name
    item_attributes = {
        "brand": "Le Collectif des Lunetiers",
        "brand_wikidata": "Q23752663",
        "name": "Le Collectif des Lunetiers",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.lecollectifdeslunetiers.fr/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/",
            headers={"X-HTTP-Method-Override": "GET"},
            data={
                "websiteId": 2462577,
                "sectionId": 2462577,
                "pageId": 2506921,
                "data": {
                    "currentStoreId": 0,
                    "distanceUnit": "kilometers",
                    "distance": "20000kilometers",
                    "coordinates": {"latitude": 0, "longitude": 0},
                },
                "dataSets": "coordinates,address,card,hours",
                "URLFormats": "canonical",
                "visualFormats": "original",
                "pagination": "0,1000",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["items"]:
            address = store["address"]["fields"]
            item = Feature()
            item["ref"] = store["common"]["code"]
            item["branch"] = store["common"]["title"].removeprefix("Le Collectif des Lunetiers ")
            item["website"] = store["common"]["URL"]["canonical"]
            item["lat"] = store["coordinates"]["latitude"]
            item["lon"] = store["coordinates"]["longitude"]
            item["street_address"] = address.get("street")
            item["postcode"] = address.get("zipCode")
            item["city"] = address.get("locality")
            item["country"] = address.get("countryCode")
            item["phone"] = store["card"].get("phone")
            item["email"] = store["card"].get("email")

            item["opening_hours"] = OpeningHours()
            for rule in store["hours"]["openingHours"]:
                day = DAYS[(rule["num"] - 1) % 7]
                times = [rule[period] for period in ["amBegin", "amEnd", "pmBegin", "pmEnd"] if rule.get(period)]
                if not times:
                    item["opening_hours"].set_closed(day)
                for open_time, close_time in zip(times[::2], times[1::2]):
                    item["opening_hours"].add_range(day, open_time, close_time)

            apply_category(Categories.SHOP_OPTICIAN, item)
            yield item
