import csv
import math

import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points


def calculate_offset_point(x, y, d, b):
    """Calculate an offset point for a given lat, lon, distance and bearing.
    formula source: https://www.movable-type.co.uk/scripts/latlong.html

    :param x: longitude in decimal degrees
    :param y: latitude in decimal degrees
    :param d: distance in km
    :param b: bearing in degrees
    :return: new x, y in decimal degrees
    """
    R = 6378.137  # km # noqa: N806
    x, y, b = math.radians(x), math.radians(y), math.radians(b)
    new_y = math.asin((math.sin(y) * math.cos(d / R)) + (math.cos(y) * math.sin(d / R) * math.cos(b)))
    new_x = x + math.atan2(
        math.sin(b) * math.sin(d / R) * math.cos(y),
        math.cos(d / R) - math.sin(y) * math.sin(new_y),
    )

    return math.degrees(new_x), math.degrees(new_y)


class ScotiabankSpider(scrapy.Spider):
    name = "scotiabank"
    allowed_domains = ["scotiabank.com"]
    item_attributes = {"brand": "Scotiabank", "brand_wikidata": "Q451476", "extras": Categories.BANK.value}
    base_url = "https://mapsms.scotiabank.com/branches?1=1&latitude={lat}&longitude={lon}&recordlimit=20&locationtypes=1&options=&languagespoken=any&language=en&address=&province=&city="
    refs = set()

    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def start_requests(self):
        with open_searchable_points("ca_centroids_100mile_radius.csv") as points:
            reader = csv.DictReader(points)
            for row in reader:
                lat, lon = row["latitude"], row["longitude"]
                yield scrapy.Request(
                    self.base_url.format(lat=lat, lon=lon),
                    meta={"request_x": lon, "request_y": lat},
                )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day, times in hours.items():
            if times["open"] and times["close"]:
                opening_hours.add_range(
                    day=day[:2],
                    open_time=times["open"],
                    close_time=times["close"],
                    time_format="%I:%M %p",
                )
        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()
        branches = (data["branchInfo"] or {}).get("marker", [])
        if branches:
            if data["branchCount"] == 20:
                refs = {x["@attributes"]["id"] for x in branches}
                if refs.issubset(self.refs):
                    return
                max_distance = branches[-1]["@attributes"]["distance"]
                # Make more requests around this location. These are angles:
                for b in [45.0, 135.0, 225.0, 315.0]:
                    new_x, new_y = calculate_offset_point(
                        x=float(response.meta["request_x"]),
                        y=float(response.meta["request_y"]),
                        d=float(max_distance),
                        b=b,
                    )
                    yield scrapy.Request(
                        self.base_url.format(lat=new_y, lon=new_x),
                        meta={"request_x": new_x, "request_y": new_y},
                    )

            for branch in branches:
                address = branch["address"]
                address1, city, state_postal, country = address.rsplit(", ", 3)
                state, postal = state_postal.rsplit(" ", 1)
                ref = branch["@attributes"]["id"]
                self.refs.add(ref)

                properties = {
                    "name": branch["name"],
                    "ref": ref,
                    "addr_full": address1.strip(", "),
                    "city": city.strip(),
                    "state": state,
                    "postcode": postal,
                    "country": country,
                    "phone": branch["phoneNo"],
                    "lat": float(branch["@attributes"]["lat"]),
                    "lon": float(branch["@attributes"]["lng"]),
                }

                hours = self.parse_hours(branch["hours"])
                if hours:
                    properties["opening_hours"] = hours

                yield Feature(**properties)
