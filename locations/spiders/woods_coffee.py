import time

import scrapy

from locations.items import Feature


class WoodsCoffeeSpider(scrapy.Spider):
    name = "woods_coffee"
    item_attributes = {
        "brand": "Woods Coffee",
        "brand_wikidata": "Q8033255",
        "country": "US",
    }
    allowed_domains = ["stockist.co"]
    start_urls = ["https://stockist.co/api/v1/u11293/locations/all"]

    def store_hours(self, hours):
        hours = hours.replace("–", "-")
        days, times = hours.split(": ")
        open_time, close_time = times.split("-")

        if "-" in days:
            start_day, end_day = days.split("-")
            days = start_day[0:2].title() + "-" + end_day[0:2].title()
        else:
            if "DAILY" in days:
                days = "Mo-Su"
            else:
                days = days[0:2].title()

        if ":" in open_time:
            open_time = time.strptime(open_time, "%I:%M %p")
        else:
            open_time = time.strptime(open_time, "%I %p")

        if ":" in close_time:
            close_time = time.strptime(close_time, "%I:%M %p")
        else:
            close_time = time.strptime(close_time, "%I %p")

        return "{days} {open}-{close}".format(
            days=days,
            open=time.strftime("%H:%M", open_time),
            close=time.strftime("%H:%M", close_time),
        )

    def parse(self, response):
        for store in response.json():
            opening_hours = ""
            for hoursMatch in store["description"].split("\n"):
                if opening_hours != "":
                    opening_hours += "; "
                opening_hours += self.store_hours(hoursMatch)

            yield Feature(
                lat=store["latitude"],
                lon=store["longitude"],
                name=store["name"],
                addr_full=", ".join(
                    filter(
                        None,
                        [
                            store["address_line_1"],
                            store["address_line_2"],
                            store["city"],
                            store["state"],
                            store["postal_code"],
                            "United States",
                        ],
                    )
                ),
                city=store["city"],
                street_address=", ".join(filter(None, [store["address_line_1"], store["address_line_2"]])),
                state=store["state"],
                postcode=store["postal_code"],
                phone=store["phone"],
                opening_hours=opening_hours,
                ref=store["id"],
            )
