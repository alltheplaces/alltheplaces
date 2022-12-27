from urllib.parse import urlencode

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import GeojsonPointItem


class DollaramaSpider(scrapy.Spider):
    name = "dollarama"
    item_attributes = {
        "brand": "Dollarama",
        "brand_wikidata": "Q3033947",
    }
    allowed_domains = ["dollarama.com"]

    def start_requests(self):
        base_url = "https://www.dollarama.com/en-CA/locations/GetDataByCoordinates?"

        params = {"distance": "100", "units": "miles"}

        with open("./locations/searchable_points/ca_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params |= {"latitude": lat, "longitude": lon}
                yield scrapy.Request(url=base_url + urlencode(params), method="POST")

    def parse_hours(self, hours):
        hrs = hours.split("|")

        opening_hours = OpeningHours()

        for day, hour in zip(DAYS, hrs):
            if hour == "Closed":
                continue
            open_time, close_time = hour.split("-")
            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for row in data.get("StoreLocations", []):

            properties = {
                "ref": row["LocationNumber"],
                "name": row["Name"],
                "addr_full": row["ExtraData"]["Address"]["AddressNonStruct_Line1"],
                "city": row["ExtraData"]["Address"]["Locality"],
                "state": row["ExtraData"]["Address"]["Region"],
                "postcode": row["ExtraData"]["Address"]["PostalCode"],
                "lat": row["Location"]["coordinates"][1],
                "lon": row["Location"]["coordinates"][0],
                "phone": row["ExtraData"]["Phone"],
            }

            if hours := self.parse_hours(row["ExtraData"]["Hours of operations"]):
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
