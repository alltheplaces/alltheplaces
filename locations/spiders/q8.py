import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class Q8Spider(scrapy.Spider):
    name = "q8"
    item_attributes = {"brand": "Q8", "brand_wikidata": "Q4119207"}
    start_urls = ["https://www.q8.be/fr/get/stations.json"]

    def parse(self, response, **kwargs):
        for store in response.json().get("Stations").get("Station"):
            opening_hours = OpeningHours()
            website = store.get("NodeURL")
            ohs = store.get("OpeningHours")
            for day, hours in ohs.items():
                if hours == "":
                    continue
                hours = hours.split("-")
                print(day, hours)
                opening_hours.add_range(day, hours[0], hours[-1])
            yield Feature(
                {
                    "ref": store.get("StationId"),
                    "name": store.get("Name"),
                    "country": store.get("Country"),
                    "street_address": " ".join(
                        filter(None, [store.get("Address_line_1"), store.get("Address_line_2")])
                    ),
                    "phone": store.get("Phone"),
                    "email": store.get("Email"),
                    "website": f"https://www.q8.be/{website}" if website else None,
                    "lat": store.get("XCoordinate"),
                    "lon": store.get("YCoordinate"),
                    "opening_hours": opening_hours,
                }
            )
