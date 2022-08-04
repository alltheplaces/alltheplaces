import scrapy
import json
import csv

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa", 7: "Su"}


class DeutschepostDeSpider(scrapy.Spider):
    name = "deutschepost_de"
    allowed_domains = ["www.deutschepost.de"]

    def start_requests(self):
        input_files = ["germany_grid_15km.csv"]
        for file in input_files:
            with open(f"./locations/searchable_points/{file}") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    yield scrapy.Request(
                        f"https://www.deutschepost.de/int-postfinder"
                        f"/postfinder_webservice/rest/v1/nearbySearch?address="
                        f"{row[0]},{row[1]}",
                        callback=self.parse,
                    )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            if hour["type"] == "OPENINGHOUR":
                if hour["timefrom"] == "24:00":
                    hour["timefrom"] = "23:59"
                if hour["timeto"] == "24:00":
                    hour["timeto"] = "23:59"
                opening_hours.add_range(
                    day=DAY_MAPPING[hour["weekday"]],
                    open_time=hour["timefrom"],
                    close_time=hour["timeto"],
                    time_format="%H:%M",
                )
        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = json.loads(response.text)
        for store in stores["pfLocations"]:
            properties = {
                "ref": store["primaryKeyDeliverySystem"],
                "name": store["locationName"],
                "addr_full": store["street"],
                "housenumber": store["houseNo"],
                "city": store["city"],
                "state": store["district"],
                "postcode": store["zipCode"],
                "country": "DE",
                "lat": store["geoPosition"]["latitude"],
                "lon": store["geoPosition"]["longitude"],
                "extras": {"locationType": store["locationType"]},
            }

            hours = self.parse_hours(store["pfTimeinfos"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
