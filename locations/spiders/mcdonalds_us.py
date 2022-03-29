# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class McDonaldsUSSpider(scrapy.Spider):
    name = "mcdonalds_us"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["www.mcdonalds.com"]

    def start_requests(self):
        # Experimentally found that 250 was max results
        base_url = "https://www.mcdonalds.com/googleappsv2/geolocation?latitude={lat}&longitude={lng}&radius=100&maxResults=250&country=us&language=en-us"

        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def store_hours(self, store_hours):
        if not store_hours:
            return None
        if all([h == "" for h in store_hours.values()]):
            return None

        day_groups = []
        this_day_group = None
        for day in (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ):
            hours = store_hours.get("hours" + day)
            if not hours:
                continue

            hours = hours.replace(" - ", "-")
            day_short = day[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day_short
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
        day_groups.append(this_day_group)

        if len(day_groups) == 1:
            opening_hours = day_groups[0]["hours"]
            if opening_hours == "04:00-04:00":
                opening_hours = "24/7"
        else:
            opening_hours = ""
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        data = response.json()

        for store in data.get("features", []):
            store_info = store["properties"]

            if store_info["addressLine4"] == "USA":

                properties = {
                    "ref": store_info["id"],
                    "addr_full": store_info["addressLine1"],
                    "city": store_info["addressLine3"],
                    "state": store_info["subDivision"],
                    "country": store_info["addressLine4"],
                    "postcode": store_info["postcode"],
                    "phone": store_info.get("telephone"),
                    "lon": store["geometry"]["coordinates"][0],
                    "lat": store["geometry"]["coordinates"][1],
                    "extras": {
                        "number": store_info[
                            "identifierValue"
                        ]  ## 4 digit identifier that is a store number for US McDonalds
                    },
                }

            else:
                properties = {
                    "ref": store_info["id"],
                    "addr_full": store_info["addressLine1"],
                    "city": store_info["addressLine3"],
                    "state": store_info["subDivision"],
                    "country": store_info["addressLine4"],
                    "postcode": store_info["postcode"],
                    "phone": store_info.get("telephone"),
                    "lon": store["geometry"]["coordinates"][0],
                    "lat": store["geometry"]["coordinates"][1],
                }

            hours = store_info.get("restauranthours")
            try:
                hours = self.store_hours(hours)
                if hours:
                    properties["opening_hours"] = hours
            except:
                self.logger.exception("Couldn't process opening hours: %s", hours)

            yield GeojsonPointItem(**properties)
