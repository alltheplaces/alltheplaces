from copy import deepcopy
from typing import AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class PorscheSpider(Spider):
    name = "porsche"
    item_attributes = {"brand": "Porsche", "brand_wikidata": "Q40993"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for country in GeonamesCache().get_countries().keys():
            for city in list(city_locations(country))[:1]:
                url = f"https://resources-nav.porsche.services/dealers/{country}?coordinates={city['latitude']},{city['longitude']}&radius=100000&unit=KM"
                yield Request(url, callback=self.parse, cb_kwargs={"country": country})

    def parse(self, response: Response, country):
        for dealer in response.json():
            shop_info = dealer.get("dealer", {})
            item = DictParser.parse(shop_info)
            item["country"] = country
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["phone"] = shop_info.get("contactDetails", {}).get("phoneNumber")
            item["email"] = shop_info.get("contactDetails", {}).get("emailAddress")
            item["website"] = shop_info.get("contactDetails", {}).get("homepage")

            if shop_info["facilityType"] != "PORSCHE_SERVICE_CENTER":
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-SHOP"
                self.parse_hours(shop_info.get("contactDetails", {}).get("contactOpeningHours"), shop_item)
                apply_category(Categories.SHOP_CAR, shop_item)
                yield shop_item

            if shop_info["facilityType"] == "PORSCHE_SERVICE_CENTER" or shop_info.get("contactDetails", {}).get(
                "serviceOpeningHours"
            ):
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-SERVICE"
                self.parse_hours(shop_info.get("contactDetails", {}).get("serviceOpeningHours"), service_item)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

    def parse_hours(self, hours: list[dict], item: Feature):
        if hours:
            oh = OpeningHours()
            for day in hours:
                if day["day"].lower() in (day.lower() for day in DAYS_FULL):
                    oh.add_range(day["day"], day["open"], day["close"])
            item["opening_hours"] = oh
