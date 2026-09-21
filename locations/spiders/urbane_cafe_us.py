import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class UrbaneCafeUSSpider(Spider):
    name = "urbane_cafe_us"
    item_attributes = {"brand": "Urbane Cafe"}
    start_urls = ["https://urbanecafe.com/locations/"]

    def parse(self, response):
        data = re.search(r"var raindrop_localize = (\{.*?\});", response.text, re.S).group(1)

        for location in json.loads(data)["locations"]:
            if "Coming Soon" in location["title"]:
                continue

            address = location["map"]
            item = Feature(
                ref=location["ID"],
                branch=location["title"],
                street_address=location["street_address"],
                city=location["city"],
                state=location["state"].strip(),
                postcode=location["zip"],
                country="US",
                lat=address["lat"],
                lon=address["lng"],
                phone=location["phone_number"],
                website=location["permalink"],
            )

            hours = OpeningHours()
            for rule in location["hours"]:
                hours.add_range(
                    rule["day_of_week"], rule["opening_hours"], rule["closing_hours"], time_format="%I:%M %p"
                )
            item["opening_hours"] = hours

            apply_category(Categories.FAST_FOOD, item)
            yield item
