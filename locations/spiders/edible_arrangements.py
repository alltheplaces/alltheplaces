import json
from datetime import datetime

import scrapy

from locations.items import Feature


class EdibleArrangementsSpider(scrapy.Spider):
    name = "edible_arrangements"
    item_attributes = {"brand": "Edible Arrangements", "brand_wikidata": "Q5337996"}
    allowed_domains = ["www.ediblearrangements.com"]

    def start_requests(self):
        yield scrapy.FormRequest(
            "https://www.ediblearrangements.com/stores/store-locator.aspx/GetStoresByCurrentLocation",
            method="POST",
            headers={
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json; charset=UTF-8",
                "origin": "https://www.ediblearrangements.com",
                "referer": "https://www.ediblearrangements.com/stores/store-locator.aspx",
                "x-requested-with": "XMLHttpRequest",
            },
            body="{'Latitude' : '37.09024' , 'Longitude': '-95.712891','Distance':'5000'}",
            callback=self.parse,
        )

    def parse(self, response):
        d = json.loads(response.json()["d"])
        for s in d["_Data"]:
            properties = {
                "lat": s["Latitude"],
                "lon": s["Longitude"],
                "phone": s["PhoneNumber"],
                "ref": s["ID"],
                "addr_full": s["MapAddress"],
                "name": s["FormalName"],
                "website": response.urljoin("/stores/" + s["PageFriendlyURL"]),
            }

            oh = []
            for h in s["TimingsShort"]:
                if h["Timing"] == "Closed":
                    continue

                days = (
                    h["Days"]
                    .replace("Monday", "Mo")
                    .replace("Tuesday", "Tu")
                    .replace("Wednesday", "We")
                    .replace("Thursday", "Th")
                    .replace("Friday", "Fr")
                    .replace("Saturday", "Sa")
                    .replace("Sunday", "Su")
                )

                from_time, to_time = h["Timing"].split("-")
                from_t = datetime.strptime(from_time.strip(), "%I:%M %p").strftime("%H:%M")
                to_t = datetime.strptime(to_time.strip(), "%I:%M %p").strftime("%H:%M")

                oh.append(f"{days} {from_t}-{to_t}")

            if oh:
                properties["opening_hours"] = "; ".join(oh)

            yield Feature(**properties)
