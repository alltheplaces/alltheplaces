from datetime import datetime
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class LidlSpider(Spider):
    name = "lidl"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}

    def make_request(self, offset: int, country: str) -> JsonRequest:
        return JsonRequest(
            "https://live.api.schwarz/odj/stores-api/v2/myapi/stores-frontend/stores?offset={}&country_code={}".format(
                offset, country
            ),
            headers={"x-apikey": "16QaHsGX3Uc3JLhNlS2ZG1CmosbzVPs2"},
            cb_kwargs={"country": country},
        )

    async def start(self) -> AsyncIterator[Any]:
        for country in [
            "AT",
            "BE",
            "BG",
            "CH",
            "CY",
            "CZ",
            "DE",
            "DK",
            "EE",
            "ES",
            "FI",
            "FR",
            "GB",
            "GR",
            "HR",
            "HU",
            "IE",
            "IT",
            "LT",
            "LU",
            "LV",
            "MT",
            "NI",
            "NL",
            "PL",
            "PT",
            "RO",
            "RS",
            "SE",
            "SI",
            "SK",
            "US",
        ]:
            yield self.make_request(0, country)

    def parse(self, response: Response, country: str, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([item.pop("housenumber"), item.pop("street")])
            item["lat"] = location["address"]["latitude"]
            item["lon"] = location["address"]["longitude"]
            item["ref"] = location["objectNumber"]

            if country == "BG":
                item["brand_wikidata"] = "Q108169047"
            elif country == "RS":
                item["brand_wikidata"] = "Q114509929"
            item["country"] = country

            features = [x["name"] for x in location["marketingData"]["infoIcons"]]
            apply_yes_no("cash_withdrawal", item, "cashBack" in features)
            apply_yes_no(Extras.TOILETS, item, "customerToilet" in features)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "diaperChangingStation" in features)
            apply_yes_no(Extras.WIFI, item, "freeWiFi" in features)
            apply_yes_no(Extras.SELF_CHECKOUT, item, "shopNGo" in features)
            apply_yes_no(Extras.WHEELCHAIR, item, "wheelchair" in features)

            try:
                item["opening_hours"] = self.parse_opening_hours(location["openingHours"])
            except Exception:
                pass

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

        meta = response.json()["meta"]
        if meta["offset"] + meta["limit"] < meta["total"]:
            yield self.make_request(meta["offset"] + meta["limit"], country)

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules["items"]:
            day = DAYS[datetime.fromisoformat(rule["date"]).weekday()]
            if rule["reason"] == "PERMANENT_CLOSING":
                oh.set_closed(day)
            elif rule["reason"] in ["REGULAR", "SUNDAY_REPEAT"]:
                for time in rule["timeRanges"]:
                    oh.add_range(day, time["from"].split("T", 1)[1], time["to"].split("T", 1)[1], "%H:%M:%S")
            elif rules["reason"] == "SPECIAL_DAY":
                raise Exception()
            else:
                self.logger.error("Unexpected opening hours reason: {}".format(rules["reason"]))
                raise Exception()

        return oh
