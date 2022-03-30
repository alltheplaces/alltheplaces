# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class McDonaldsSpider(scrapy.Spider):
    name = "mcdonalds"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["www.mcdonalds.com"]
    start_urls = (
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=44.97&longitude=-93.21&radius=100000&maxResults=300000&country=us&language=en-us",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=44.97&longitude=-93.21&radius=100000&maxResults=300000&country=ca&language=en-ca",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=44.97&longitude=-93.21&radius=100000&maxResults=300000&country=gb&language=en-gb",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=44.97&longitude=-93.21&radius=100000&maxResults=300000&country=se&language=sv-se",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=55.9394691&longitude=10.17994550000003&radius=100000&maxResults=300000&country=dk&language=da-dk",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=60.7893233&longitude=10.689804200000026&radius=100000&maxResults=300000&country=no&language=en-no",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=24.0799008&longitude=45.29000099999996&radius=100000&maxResults=300000&country=saj&language=en-sa",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=29.3365728&longitude=47.67552909999995&radius=100000&maxResults=300000&country=kw&language=en-kw",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=24.1671413&longitude=56.114225300000044&radius=100000&maxResults=300000&country=om&language=en-om",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=23.659703&longitude=53.7042189&radius=100000&maxResults=300000&country=ae&language=en-ae",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=26.1621079&longitude=50.4501947&radius=100000&maxResults=300000&country=bh&language=en-bh",
        "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude=25.2854473&longitude=51.53103979999992&radius=100000&maxResults=300000&country=qa&language=en-q",
    )

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
