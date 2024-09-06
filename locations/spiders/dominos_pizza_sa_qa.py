from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.pipelines.address_clean_up import clean_address


class DominosPizzaSAQASpider(Spider):
    name = "dominos_pizza_sa_qa"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for country_code, name, lat, lon in [
            ("QA", "QATAR", "25.4477038", "51.1814573"),
            ("SA", "SAUDI_ARABIA", "25.8517475", "43.52223129999993"),
        ]:
            url = f"https://order.golo03.dominos.com/store-locator-international/locate/store?regionCode={country_code}&latitude={lat}&longitude={lon}"
            headers = {"DPZ-Language": "en", "DPZ-Market": name}

            yield JsonRequest(url=url, headers=headers, callback=self.parse, cb_kwargs={"country_code": country_code})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["Stores"]:
            item = DictParser.parse(store)
            item["addr_full"] = clean_address(store["AddressDescription"])
            item["country"] = kwargs["country_code"]
            item["website"] = f'https://www.dominos.{kwargs["country_code"].lower()}'
            item["branch"] = item.pop("name")
            item["street_address"] = store["LocationInfo"]
            item["opening_hours"] = OpeningHours()
            if hours_string := store["HoursDescription"]:
                for rule in hours_string.splitlines():
                    days, times = rule.split(" ", 1)
                    for days_period in days.split(","):
                        for time_period in times.split(","):
                            if time_period == "00:00-00:00":
                                continue
                            item["opening_hours"].add_days_range(
                                day_range(*days_period.split("-")) if "-" in days_period else [days_period],
                                *time_period.split("-"),
                            )

            yield item
