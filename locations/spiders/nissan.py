import locale
import re

import scrapy

from locations.categories import Categories
from locations.country_utils import CountryUtils
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


# Although API url appears to be covering EU only, but actually scrapes multiple non EU countries as well.
class NissanSpider(scrapy.Spider):
    name = "nissan"
    item_attributes = {"brand": "Nissan", "brand_wikidata": "Q20165", "extras": Categories.SHOP_CAR.value}

    def __init__(self):
        self._countries = CountryUtils().gc.get_countries_by_names()

    def start_requests(self):
        for loc in locale.locale_alias.keys():
            if not re.fullmatch("[a-z]{2}_[a-z]{2}", loc):
                continue
            loc = loc[:3] + loc[3:].upper()
            yield scrapy.Request(
                url=f"https://eu.nissan-api.net/v2/publicAccessToken?locale={loc}&scope=READ&proxy=*&brand=nissan&environment=prod",
                headers={"origin": "https://www.nissan-global.com"},
                callback=self.parse_token,
            )

    def parse_token(self, response, **kwargs):
        token = response.json()["access_token"]
        yield scrapy.Request(
            url="https://eu.nissan-api.net/v2/dealers?size=-1&include=openingHours",
            headers={"accesstoken": f"Bearer {token}"},
            callback=self.parse_dealers,
            dont_filter=True,
        )

    def parse_dealers(self, response, **kwargs):
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
            yield item

    @staticmethod
    def _clean_time(time: str) -> str:
        # Some times are "." separated, e.g. "08.00"
        # Some times are missing the minutes, e.g. "12"
        # Some times have seconds, e.g. "08:00:00"

        time = time.strip()
        hours, minutes, *_ = re.split("[:.]", time + ":00")
        return hours + ":" + minutes
