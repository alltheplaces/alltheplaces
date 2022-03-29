import scrapy
from locations.items import GeojsonPointItem
from urllib.parse import urlencode
from scrapy.selector import Selector
from locations.hours import OpeningHours

Days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]


class DollaramaSpider(scrapy.Spider):
    name = "dollarama"
    item_attributes = {"brand": "Dollarama"}
    allowed_domains = ["dollarama.com"]

    def start_requests(self):
        base_url = "https://www.dollarama.com/en-CA/locations/anydata-api?"

        params = {"distance": "100", "units": "miles"}

        with open(
            "./locations/searchable_points/ca_centroids_100mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params.update({"latitude": lat, "longitude": lon})
                yield scrapy.Request(url=base_url + urlencode(params))

    def parse_hours(self, hours):
        hrs = hours.split("|")

        opening_hours = OpeningHours()

        for day, hour in zip(Days, hrs):
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

            hours = self.parse_hours(row["ExtraData"]["Hours of operations"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
