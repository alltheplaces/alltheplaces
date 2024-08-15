import json
import re
from urllib.parse import urlencode

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points

DAY_MAPPING = {
    "Sun": "Su",
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
}
DAY_ORDER = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


class BarnesAndNobleSpider(scrapy.Spider):
    name = "barnes_and_noble"
    item_attributes = {"brand": "Barnes and Noble"}
    allowed_domains = [
        "stores.barnesandnoble.com",
    ]

    def start_requests(self):
        base_url = "https://stores.barnesandnoble.com/stores?"

        params = {"storeFilter": "all", "v": "1", "view": "map"}

        with open_searchable_points("us_centroids_50mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params.update({"lat": lat, "lng": lon})
                yield scrapy.Request(url=base_url + urlencode(params))

    def parse_hours(self, hours):
        """Sun-Thu 9-9, Fri&Sat 9-10"""
        o = OpeningHours()
        ranges = hours.split(",")
        for range in ranges:
            pattern = r"(.{3})[-&](.{3})\s([\d:]+)-([\d:]+)"
            start_day, end_day, start_time, end_time = re.search(pattern, range.strip()).groups()
            if ":" not in start_time:
                start_time += ":00 AM"
            if ":" not in end_time:
                end_time += ":00 PM"
            for day in DAY_ORDER[DAY_ORDER.index(start_day) : DAY_ORDER.index(end_day) + 1]:
                o.add_range(
                    day=DAY_MAPPING[day],
                    open_time=start_time,
                    close_time=end_time,
                    time_format="%I:%M %p",
                )
        return o.as_opening_hours()

    def parse(self, response):
        data = response.xpath('//div[@id="mapDiv"]/script/text()').re(r"storesJson\s=\s(.*?);")
        if not data:
            if "No results found" in response.xpath('//div[@class="content"]/h3/text()').extract_first():
                return

        stores = json.loads(data[0])

        for store in stores:
            address = store.get("address2", None)
            if not address:
                address = store.get("address1")  # address1 is usually the venue/mall name

            properties = {
                "name": store["name"],
                "addr_full": address,
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "phone": store["phone"],
                "ref": store["storeId"],
                "website": "https://stores.barnesandnoble.com/store/{}".format(store["storeId"]),
                "lat": float(store["location"][1]),
                "lon": float(store["location"][0]),
            }

            try:
                opening_hours = self.parse_hours(store["hours"])
            except:
                opening_hours = None
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield Feature(**properties)
