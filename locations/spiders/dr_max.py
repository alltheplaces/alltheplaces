from datetime import datetime
from zoneinfo import ZoneInfo

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DrMaxSpider(scrapy.Spider):
    name = "dr_max"
    item_attributes = {"brand": "Dr. Max", "brand_wikidata": "Q56317371"}

    start_urls = [
        "https://pharmacy.drmax.pl/api/v1/public/pharmacies",
        "https://pharmacy.drmax.cz/api/v1/public/pharmacies",
        "https://pharmacy.drmax.sk/api/v1/public/pharmacies",
        "https://pharmacy.drmax.it/api/v1/public/pharmacies",
    ]

    website_roots = [
        "https://www.drmax.pl/apteki/",
        "https://www.drmax.cz/lekarny/",
        "https://www.drmax.sk/lekarne/",
        "https://www.drmax.it/le-nostre-farmacie/",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            tld = response.url.split("/")[2].split(".")[-1]

            # copy location.location to the root of the object
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item.pop("street")
            item["street_address"] = location["street"]
            item["name"] = location["pharmacyPublicName"]
            if len(location["phoneNumbers"]) > 0:
                item["phone"] = location["phoneNumbers"][0]["number"]
            item["email"] = location.get("additionalParams").get("email")
            item["image"] = location["pharmacyImage"]
            item["country"] = tld
            service_ids = [service["serviceId"] for service in location["services"]]
            apply_yes_no(Extras.WHEELCHAIR, item, "WHEELCHAIR_ACCESS" in service_ids)
            root_url = self.website_roots[self.start_urls.index(response.url)]
            item["website"] = root_url + location["urlKey"]

            item["opening_hours"] = OpeningHours()
            opening_days = location["openingHours"]
            for day in opening_days:
                if not day["open"]:
                    continue
                # day in the format: "2009-01-02T00:00:00Z"
                day_date_str = day["date"]
                weekday = datetime.strptime(day_date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%A")
                if day["nonstop"]:
                    item["opening_hours"].add_range(weekday, "00:00", "23:59")
                    continue
                for opening_hours in day["openingHour"]:
                    if not opening_hours["open"]:
                        continue

                    open_time = self.calculate_local_time(opening_hours["from"], item)
                    close_time = self.calculate_local_time(opening_hours["to"], item)
                    if open_time and close_time:
                        item["opening_hours"].add_range(weekday, open_time, close_time)

            yield item

    def calculate_local_time(self, date_string, item) -> str:
        local_timezone = None
        if item["country"].lower() == "cz":
            local_timezone = "Europe/Prague"
        elif item["country"].lower() == "sk":
            local_timezone = "Europe/Bratislava"
        elif item["country"].lower() == "it":
            local_timezone = "Europe/Rome"
        elif item["country"].lower() == "pl":
            local_timezone = "Europe/Warsaw"
        else:
            return None
        local_timezone = ZoneInfo(local_timezone)
        local_time = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").astimezone(local_timezone)
        return local_time.strftime("%H:%M")
