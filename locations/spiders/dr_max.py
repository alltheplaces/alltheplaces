from datetime import datetime
from typing import Any, Iterable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DrMaxSpider(scrapy.Spider):
    name = "dr_max"
    item_attributes = {"brand": "Dr. Max", "brand_wikidata": "Q56317371"}
    store_locators = {
        "pl": "https://www.drmax.pl/apteki/",
        "cz": "https://www.drmax.cz/lekarny/",
        "sk": "https://www.drmax.sk/lekarne/",
        "it": "https://www.drmax.it/le-nostre-farmacie/",
        "ro": "https://www.drmax.ro/farmacii/",
    }

    def start_requests(self) -> Iterable[Request]:
        for country in self.store_locators:
            yield JsonRequest(
                url=f"https://pharmacy.drmax.{country}/api/v1/public/pharmacies",
                meta=dict(country=country),
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item["ref"] = location["urlKey"]  # id is not unique globally
            item["street_address"] = item.pop("street")
            item["name"] = location["pharmacyPublicName"]
            if len(location["phoneNumbers"]) > 0:
                item["phone"] = location["phoneNumbers"][0]["number"]
            item["email"] = location.get("additionalParams").get("email")
            item["image"] = location["pharmacyImage"]
            item["country"] = country = response.meta["country"]
            service_ids = [service["serviceId"] for service in location["services"]]
            apply_yes_no(Extras.WHEELCHAIR, item, "WHEELCHAIR_ACCESS" in service_ids)
            item["website"] = urljoin(self.store_locators[country], location["urlKey"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]:
                if not rule["open"]:
                    continue
                if rule["nonstop"]:
                    weekday = datetime.strptime(rule["date"], "%Y-%m-%dT%H:%M:%SZ").strftime("%A")
                    item["opening_hours"].add_range(weekday, "00:00", "23:59")
                else:
                    for opening_hours in rule["openingHour"]:
                        if not opening_hours["open"]:
                            continue
                        weekday = datetime.strptime(opening_hours["from"], "%Y-%m-%dT%H:%M:%SZ").strftime("%A")
                        if opening_hours["from"] and opening_hours["to"]:
                            open_time = self.calculate_local_time(opening_hours["from"], country)
                            close_time = self.calculate_local_time(opening_hours["to"], country)
                            if open_time and close_time:
                                item["opening_hours"].add_range(weekday, open_time, close_time)

            yield item

    def calculate_local_time(self, date_string: str, country: str) -> str:
        local_timezone = None
        if country == "cz":
            local_timezone = "Europe/Prague"
        elif country == "sk":
            local_timezone = "Europe/Bratislava"
        elif country == "it":
            local_timezone = "Europe/Rome"
        elif country == "pl":
            local_timezone = "Europe/Warsaw"
        elif country == "ro":
            local_timezone = "Europe/Bucharest"
        else:
            return ""
        local_timezone = ZoneInfo(local_timezone)
        local_time = (
            datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=ZoneInfo("UTC"))
            .astimezone(local_timezone)
        )
        return local_time.strftime("%H:%M")
