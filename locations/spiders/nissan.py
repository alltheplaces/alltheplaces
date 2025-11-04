import locale
import re
from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import CountryUtils
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


# Although API url appears to be covering EU only, but actually scrapes multiple non EU countries as well.
class NissanSpider(scrapy.Spider):
    name = "nissan"
    BRANDS = {
        "nissan": {"brand": "Nissan", "brand_wikidata": "Q20165"},
        "infiniti": {"brand": "Infiniti", "brand_wikidata": "Q29714"},
    }
    # Each country has its own set of service IDs, it's a bit tedious to map them all,
    # so just mapping the known ones for now.
    CAR_SALES_IDS = ["de_nissan_NCD", "us_en_nissan_S_SLS"]
    CAR_SERVICE_IDS = ["de_nissan_AR", "de_nissan_KL", "us_en_nissan_S_CLSN", "us_en_nissan_S_ES", "us_en_nissan_S_SVC"]
    USED_CAR_SALES_IDS = ["de_nissan_UV", "us_en_nissan_S_CPO"]

    def __init__(self) -> None:
        self._countries = CountryUtils().gc.get_countries_by_names()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for brand in self.BRANDS:
            for loc in locale.locale_alias.keys():
                if not re.fullmatch("[a-z]{2}_[a-z]{2}", loc):
                    continue
                loc = loc[:3] + loc[3:].upper()
                yield JsonRequest(
                    url=f"https://eu.nissan-api.net/v2/publicAccessToken?locale={loc}&scope=READ&proxy=*&brand={brand}&environment=prod",
                    headers={"origin": "https://www.nissan-global.com"},
                    callback=self.parse_token,
                    cb_kwargs={"brand": brand},
                )

    def parse_token(self, response: Response, brand: str) -> Any:
        token = response.json()["access_token"]
        yield JsonRequest(
            url="https://eu.nissan-api.net/v2/dealers?size=-1&include=openingHours",
            headers={"accesstoken": f"Bearer {token}"},
            callback=self.parse_dealers,
            cb_kwargs={"brand": brand},
            dont_filter=True,
        )

    def parse_dealers(self, response: Response, brand: str) -> Any:
        for dealer in response.json()["dealers"]:
            dealer["id"] = dealer.pop("dealerId")
            item = DictParser.parse(dealer)
            if item["state"] in self._countries:
                item["country"] = item.pop("state")
            for w in dealer["contact"].get("websites", []):
                item["website"] = w.get("url")
                break

            oh = OpeningHours()
            for day in dealer.get("openingHours", {}).get("regularOpeningHours", []):
                for interval in day.get("openIntervals", []):
                    oh.add_range(
                        # weekDay is 1 to 7, 1 being Monday
                        day=DAYS[day["weekDay"] - 1],
                        open_time=self._clean_time(interval["openFrom"]),
                        close_time=self._clean_time(interval["openUntil"]),
                        time_format="%H:%M",
                    )
            item["opening_hours"] = oh
            item.update(self.BRANDS[brand])

            services = [s["id"] for s in dealer.get("services", [])]

            if self.is_car_sales(services):
                sales_item = item.deepcopy()
                sales_item["ref"] = f"{item['ref']}-sales"
                apply_category(Categories.SHOP_CAR, sales_item)
                apply_yes_no(Extras.USED_CAR_SALES, sales_item, self.is_used_car_sales(services))
                apply_yes_no(Extras.CAR_REPAIR, sales_item, self.is_car_service(services))
                yield sales_item

            if self.is_car_service(services):
                service_item = item.deepcopy()
                service_item["ref"] = f"{item['ref']}-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

            if not (self.is_car_sales(services) or self.is_car_service(services)):
                # Fallback for locations that don't have mapping at the moment
                apply_category(Categories.SHOP_CAR, item)
                yield item

    def is_car_sales(self, services: list[str]) -> bool:
        return any(s in services for s in self.CAR_SALES_IDS + self.USED_CAR_SALES_IDS)

    def is_car_service(self, services: list[str]) -> bool:
        return any(s in services for s in self.CAR_SERVICE_IDS)

    def is_used_car_sales(self, services: list[str]) -> bool:
        return any(s in services for s in self.USED_CAR_SALES_IDS)

    @staticmethod
    def _clean_time(time: str) -> str:
        # Some times are "." separated, e.g. "08.00"
        # Some times are missing the minutes, e.g. "12"
        # Some times have seconds, e.g. "08:00:00"

        time = time.strip()
        hours, minutes, *_ = re.split("[:.]", time + ":00")
        return hours + ":" + minutes
