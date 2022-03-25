# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.redrobin.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "*/*",
    "Referer": "https://www.redrobin.com/",
    "Content-Type": "application/json",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "x-api-key": "Dx3zjnmVaT2Rvhbs8cwLB8ER0SvwaxmZ1cwSmZ4e",
    "authorization": "none",
}


class RedRobinSpider(scrapy.Spider):

    name = "red_robin"
    item_attributes = {"brand": "Red Robin", "brand_wikidata": "Q7304886"}

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(",")

                form_data = {
                    "operationName": "RestaurantQueries",
                    "variables": {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "radius": 200,
                    },
                    "query": "query RestaurantQueries($latitude: Float!, $longitude: Float!, $radius: Float!) {\n  restaurants {\n    byGeolocation(latitude: $latitude, longitude: $longitude, radius: $radius) {\n      ...LocationCard\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment LocationCard on RestaurantResult {\n  distance\n  restaurant {\n    ...RestaurantDetails\n    __typename\n  }\n  __typename\n}\n\nfragment RestaurantDetails on RestaurantInfo {\n  address {\n    ...Address\n    __typename\n  }\n  bannerImage {\n    ...BannerImage\n    __typename\n  }\n  gallery {\n    ...GalleryImage\n    __typename\n  }\n  events {\n    ...RestaurantEvent\n    __typename\n  }\n  capabilities\n  franchiseName\n  franchiseSlug\n  geoCoordinate {\n    latitude\n    longitude\n    __typename\n  }\n  id\n  name\n  phone\n  temporarilyClosed\n  timezone\n  statusValue\n  serviceHours {\n    ...RestaurantServiceHours\n    __typename\n  }\n  slug\n  uri\n  waitlistAvailable\n  ...LocationLinks\n  __typename\n}\n\nfragment BannerImage on ImageSet {\n  alt\n  height\n  url\n  width\n  sourceSet(queryList: [{format: WEBP, quality: 50, width: 410}, {width: 410}, {format: WEBP, quality: 50, width: 820}, {width: 820}, {format: WEBP, quality: 50, width: 1680}, {width: 1680}]) {\n    format\n    url\n    width\n    height\n    __typename\n  }\n  __typename\n}\n\nfragment GalleryImage on ImageSet {\n  alt\n  height\n  url\n  width\n  sourceSet(queryList: [{format: WEBP, quality: 50, width: 410}, {width: 410}, {format: WEBP, quality: 50, width: 540}, {width: 540}, {format: WEBP, quality: 50, width: 910}, {width: 910}]) {\n    format\n    url\n    width\n    height\n    __typename\n  }\n  __typename\n}\n\nfragment RestaurantEvent on RestaurantEvent {\n  startTime\n  endTime\n  legal\n  title\n  details\n  anchorId\n  __typename\n}\n\nfragment LocationLinks on RestaurantInfo {\n  onlineOrderingLink\n  cateringLink\n  careersLink\n  __typename\n}\n\nfragment Address on Address {\n  line1\n  line2\n  city\n  state\n  country\n  zipCode\n  __typename\n}\n\nfragment RestaurantServiceHours on RestaurantServiceHours {\n  restaurantHours {\n    ...RestaurantServiceWorkingHour\n    __typename\n  }\n  deliveryHours {\n    ...RestaurantServiceWorkingHour\n    __typename\n  }\n  pickupHours {\n    ...RestaurantServiceWorkingHour\n    __typename\n  }\n  __typename\n}\n\nfragment RestaurantServiceWorkingHour on RestaurantServiceWorkingHour {\n  close\n  day\n  description\n  open\n  special\n  __typename\n}\n",
                }

                yield scrapy.http.FormRequest(
                    url="https://api.burgerblaster.io/graphql",
                    method="POST",
                    body=json.dumps(form_data),
                    headers=HEADERS,
                    callback=self.parse,
                )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["day"][:2].title()
            open_time = hour["open"]
            close_time = hour["close"]

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for place in results["data"]["restaurants"]["byGeolocation"]:
            properties = {
                "ref": place["restaurant"]["id"],
                "name": place["restaurant"]["name"],
                "addr_full": place["restaurant"]["address"]["line1"],
                "city": place["restaurant"]["address"]["city"],
                "state": place["restaurant"]["address"]["state"],
                "postcode": place["restaurant"]["address"]["zipCode"],
                "country": place["restaurant"]["address"]["country"],
                "lat": place["restaurant"]["geoCoordinate"]["latitude"],
                "lon": place["restaurant"]["geoCoordinate"]["longitude"],
                "phone": place["restaurant"]["phone"],
                "website": "https://www.redrobin.com/locations"
                + place["restaurant"]["uri"],
            }

            hours = self.parse_hours(
                place["restaurant"]["serviceHours"]["restaurantHours"]
            )
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
