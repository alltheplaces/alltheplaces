import scrapy

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AlbertAndWalterSpider(scrapy.Spider):
    name = "albert_and_walter"
    item_attributes = {"brand": "A&W", "brand_wikidata": "Q2818848"}
    start_urls = ["https://web.aw.ca/api/locations/"]

    def parse(self, response, **kwargs):
        for data in response.json():
            properties = {
                "ref": data["restnum"],
                "name": data["restaurant_name"],
                "lat": data["latitude"],
                "lon": data["longitude"],
                "street_address": data["public_address"],  # data['address1'] + ' ' + data['address2'],
                "city": data["city_name"],
                "state": data["province_code"],
                "postcode": data["postal_code"],
                "phone": data["phone_number"],
                "opening_hours": OpeningHours(),
            }

            for day, hours in enumerate(data["hours"]):
                start_time, end_time = hours.split("-")
                properties["opening_hours"].add_range(DAYS[day - 1], start_time, end_time, time_format="%I:%M:%S %p")

            properties["website"] = "/".join(
                [
                    "https://web.aw.ca/en/locations",
                    data["restnum"],
                    data["city_name"].replace(".", "").replace("'", "").replace(" ", "-").lower(),
                    data["slug"],
                ]
            )

            apply_yes_no(Extras.DRIVE_THROUGH, properties, data["drive_thru"] == "Y")

            yield Feature(**properties)
