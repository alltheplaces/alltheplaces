from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class CccSpider(Spider):
    name = "ccc"
    item_attributes = {"brand": "CCC", "brand_wikidata": "Q11788344"}
    # Country code of each ccc.eu market, mapped to the frontend ID
    markets = {
        "BG": 84,
        "CZ": 67,
        "EE": 48,
        "HR": 54,
        "HU": 80,
        "LT": 47,
        "LV": 46,
        "PL": 44,
        "RO": 75,
        "RS": 90,
        "SI": 37,
        "SK": 58,
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country, frontend_id in self.markets.items():
            yield JsonRequest(
                url=f"https://ccc.eu/{country.lower()}/api/Configuration/GetShops",
                headers={"x-frontend-id": str(frontend_id)},
                cb_kwargs={"country": country},
            )

    def parse(self, response: Response, country: str) -> Iterable[Feature]:
        for shop in response.json()["data"]:
            item = DictParser.parse(shop)
            item["ref"] = shop["shopNumber"]
            item["branch"] = shop["shopName"].removeprefix(f"CCC {shop['shopNumber']} ")
            item["street_address"] = item.pop("street")
            item["country"] = country

            item["opening_hours"] = OpeningHours()
            for days, hours in [
                (DAYS_WEEKDAY, shop["openingHours"]),
                (["Sa"], shop["openingHoursSaturday"]),
                (["Su"], shop["openingHoursSunday"]),
            ]:
                open_time, close_time = hours.split(" - ")
                item["opening_hours"].add_days_range(days, open_time, close_time)

            apply_category(Categories.SHOP_SHOES, item)

            yield item
