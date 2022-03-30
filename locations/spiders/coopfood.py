import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CoopFoodSpider(scrapy.Spider):
    name = "coopfood"
    item_attributes = {"brand": "Co-op Food", "brand_wikidata": "Q3277439"}
    allowed_domains = ["coop.co.uk"]
    download_delay = 0.5
    page_number = 1
    start_urls = (
        "https://www.coop.co.uk/store-finder/api/locations/food?location=54.9966124%2C-7.308574799999974&distance=30000000000&always_one=true&format=json",
    )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            open_time = hour["opens"]
            close_time = hour["closes"]
            if hour["type"] == "24_hour":
                close_time = "23:59"
            try:
                opening_hours.add_range(
                    day=hour["name"][:2], open_time=open_time, close_time=close_time
                )
            except:  # no opening hours
                continue
        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["results"]:
            open_hours = self.parse_hours(store["opening_hours"])

            properties = {
                "ref": store["url"],
                "name": store["name"],
                "opening_hours": open_hours,
                "website": "https://www.coop.co.uk" + store["url"],
                "addr_full": " ".join(
                    [
                        store["street_address"],
                        store["street_address2"],
                        store["street_address3"],
                    ]
                ),
                "city": store["town"],
                "postcode": store["postcode"],
                "country": "United Kingdom",
                "lon": float(store["position"]["x"]),
                "lat": float(store["position"]["y"]),
                "phone": store["phone"],
            }

            yield GeojsonPointItem(**properties)

        if data["next"] is not None:
            self.page_number = self.page_number + 1
            yield scrapy.Request(self.start_urls[0] + "&page=" + str(self.page_number))
