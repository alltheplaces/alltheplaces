import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.q8_italia import Q8ItaliaSpider


# AKA Q8 NWE https://www.q8.be/nl/stations
class Q8Spider(scrapy.Spider):
    name = "q8"
    start_urls = ["https://www.q8.be/fr/get/stations.json"]

    BRANDS = {
        "EASY": {"brand": "Q8 Easy", "brand_wikidata": "Q1806948"},
        "Q8": Q8ItaliaSpider.item_attributes,
    }

    def parse(self, response, **kwargs):
        for store in response.json().get("Stations").get("Station"):
            opening_hours = OpeningHours()
            website = store.get("NodeURL")
            ohs = store.get("OpeningHours")
            for day, hours in ohs.items():
                if hours == "":
                    continue
                for period in hours.split(" "):
                    start_time, end_time = period.split("-")
                    opening_hours.add_range(day, start_time, end_time)
            item = Feature(
                {
                    "ref": store.get("StationId"),
                    "name": store.get("Name"),
                    "country": store.get("Country"),
                    "addr_full": ", ".join(filter(None, [store.get("Address_line_1"), store.get("Address_line_2")])),
                    "phone": store.get("Phone"),
                    "email": store.get("Email"),
                    "website": f"https://www.q8.be/{website}" if website else None,
                    "lat": store.get("XCoordinate"),
                    "lon": store.get("YCoordinate"),
                    "opening_hours": opening_hours,
                }
            )

            if brand := self.BRANDS.get(store["Category"]):
                item.update(brand)
            apply_category(Categories.FUEL_STATION, item)
            yield item
