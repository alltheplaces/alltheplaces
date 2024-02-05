import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_SE, OpeningHours, sanitise_day
from locations.items import Feature


class NordeaSeSpider(scrapy.Spider):
    name = "nordea_se"
    item_attributes = {"brand": "Nordea", "brand_wikidata": "Q1123823"}
    start_urls = [
        "https://bank.nordea.se/wemapp/api/bl2/markersdesktop?language=sv&country=se&type=all&swlat=48.62106214708822&swlng=-64.9736865&nelat=68.88121906615748&nelng=102.2606885&clat=60.12816&clng=18.64350&category=all&_=1677934421045"
    ]

    def parse(self, response):
        for bank in response.json().get("listItems"):
            oh = OpeningHours()
            for row in bank.get("openingHoursRegular").split("<br />"):
                hours = re.findall(r": [0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}|: Stängt", row)[0]
                days = row.replace(hours, "")
                for day in days.split(", "):
                    if (hours := hours.replace(": ", "")) == "Stängt":
                        continue
                    oh.add_range(
                        day=sanitise_day(day, {**DAYS_SE}),
                        open_time=hours.split("-")[0],
                        close_time=hours.split("-")[1],
                    )
            item = Feature()
            item["ref"] = bank.get("id")
            item["street_address"] = bank.get("address", {}).get("street_address")
            item["state"] = bank.get("address", {}).get("region")
            item["postcode"] = bank.get("address", {}).get("postal_code")
            item["lat"] = bank.get("lat")
            item["lon"] = bank.get("lng")
            item["opening_hours"] = oh.as_opening_hours()
            apply_category(Categories.BANK, item)

            yield item
