# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import date
from urllib.parse import urlparse, parse_qsl


from locations.items import GeojsonPointItem


class BestBuyMexicoSpider(scrapy.Spider):
    name = "bestbuy-mx"
    item_attributes = {"brand": "Best Buy"}
    allowed_domains = [
        "www.bestbuy.com.mx",
    ]
    bb_url = "http://www.bestbuy.com.mx/storelocator/api/{}"

    starting_zip_codes = [
        "06010",
        "97130",
        "44840",
        "66260",
        "94294",
        "55076",
    ]
    bb_urls = list()
    for z in starting_zip_codes:
        bb_urls.append(bb_url.format(z))
    start_urls = tuple(bb_urls)
    completed_requests = set()

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for i, line in enumerate(store_hours):
            for key, value in line.items():
                if key == "dateOpen":
                    match = re.search(r"^(\d{1,4})-(\d{1,2})-(\d{1,2})$", value)
                    (y, m, d) = match.groups()
                    day = date(int(y), int(m), int(d)).strftime("%A")
                if key == "timeOpen":
                    hours = value
                if key == "timeClosed":
                    hours += "-" + value
            # Store hours has 2 weeks of data
            if i >= 7:
                break

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        if this_day_group:
            day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Mo" and day_group["to_day"] == "Su":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]
        return opening_hours

    def parse(self, response):
        data = response.json()["data"]["stores"]

        bounding_box = {
            "min_lat": 100,
            "max_lat": -100,
            "min_lon": 300,
            "max_lon": -300,
            "min_lat_zip": None,
            "max_lat_zip": None,
            "min_lon_zip": None,
            "max_lon_zip": None,
        }

        for store in data:
            # Door# is at the end in address format in Spanish
            parts = store["addr1"].split(" ")
            num = ""
            for part in parts:
                try:
                    num = "%d" % int(part)
                except ValueError:
                    pass
            # strip out the door number from address for street name
            street = store["addr1"].replace(num, "")
            properties = {
                "phone": store["phone"],
                "ref": store["id"],
                "name": store["name"],
                "opening_hours": self.store_hours(store["hours"]),
                "lat": store["latitude"],
                "lon": store["longitude"],
                "addr_full": store["addr1"] + ", " + store["addr2"],
                "housenumber": num,
                "street": street,
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postalCode"],
                "country": store["country"],
                "website": store["links"]["self"]["href"],
            }
            lat = float(store["latitude"])
            lon = float(store["longitude"])
            if lat < bounding_box["min_lat"]:
                bounding_box["min_lat"] = lat
                bounding_box["min_lat_zip"] = store["postalCode"]
            if lat > bounding_box["max_lat"]:
                bounding_box["max_lat"] = lat
                bounding_box["max_lat_zip"] = store["postalCode"]
            if lon < bounding_box["min_lon"]:
                bounding_box["min_lon"] = lon
                bounding_box["min_lon_zip"] = store["postalCode"]
            if lon > bounding_box["max_lon"]:
                bounding_box["max_lon"] = lon
                bounding_box["max_lon_zip"] = store["postalCode"]

            yield GeojsonPointItem(**properties)

        for key, value in bounding_box.items():
            if "zip" in key and value is not None:
                if value in self.completed_requests:
                    self.logger.info(
                        "Skipping request for zipcode %s because we already did it",
                        value,
                    )
                else:
                    self.completed_requests.add(value)
                    yield scrapy.Request(self.bb_url.format(value))
