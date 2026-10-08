import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Overseas stores are listed with countryCode "FR"
OVERSEAS_COUNTRIES = {"97150": "MF", "971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class LaGrandeRecreFRSpider(Spider):
    name = "la_grande_recre_fr"
    item_attributes = {"brand": "La Grande Récré", "brand_wikidata": "Q3209556", "name": "La Grande Récré"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.lagranderecre.fr/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/",
            headers={"X-HTTP-Method-Override": "GET"},
            data={
                "websiteId": 100052,
                "sectionId": 100890,
                "pageId": 100696,
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
                "referer": "https://www.lagranderecre.fr/magasins/",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["items"]:
            address = store["address"]["fields"]
            item = Feature()
            item["ref"] = store["common"]["code"]
            item["branch"] = re.sub(r"^La Grande R[ée]cr[ée]\s*", "", store["common"]["title"], flags=re.IGNORECASE)
            item["website"] = store["common"]["URL"]["canonical"]
            item["lat"] = store["coordinates"]["latitude"]
            item["lon"] = store["coordinates"]["longitude"]
            item["street_address"] = address.get("street")
            item["postcode"] = address.get("zipCode")
            item["city"] = address.get("locality")
            item["country"] = address.get("countryCode")
            postcode = item["postcode"] or ""
            if country := OVERSEAS_COUNTRIES.get(postcode) or OVERSEAS_COUNTRIES.get(postcode[:3]):
                item["country"] = country
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

            apply_category(Categories.SHOP_TOYS, item)
            yield item
