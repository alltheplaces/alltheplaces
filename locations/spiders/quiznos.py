import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class QuiznosSpider(scrapy.Spider):
    name = "quiznos"
    item_attributes = {"brand": "Quiznos", "brand_wikidata": "Q1936229"}
    allowed_domains = ["restaurants.quiznos.com"]
    start_urls = (
        "https://restaurants.quiznos.com/api/stores-by-bounds?bounds={%22south%22:-90,%22west%22:-180,%22north%22:90,%22east%22:180}",
    )

    def parse(self, response):
        for store in response.json():
            hours = OpeningHours()

            for day in DAYS:
                start_time = store["hour_open_" + day]
                end_time = store["hour_close_" + day]
                if start_time == end_time == "Closed":
                    continue
                if start_time == end_time == "Open 24 Hours":
                    start_time = end_time = "12:00 AM"
                hours.add_range(day[:2].capitalize(), start_time, end_time, "%I:%M %p")

            properties = {
                "lat": store["latitude"],
                "lon": store["longitude"],
                "ref": store["number"],
                "website": store["order_url"],
                "phone": store["phone_number"],
                "name": store["name"],
                "opening_hours": hours.as_opening_hours(),
                "street_address": store["address_line_1"],
                "extras": {"addr:suite": store["address_line_2"]},
                "city": store["city"],
                "state": store["province"],
                "postcode": store["postal_code"],
                "country": store["country"],
            }

            yield Feature(**properties)
