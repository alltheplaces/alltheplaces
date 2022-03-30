# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

# When the 7-eleven site loads, it makes a reqest to fetch an anon
# OAuth bearer token from the API using this client ID / secret.
#
# If this key rotates in the future, load the site in a private window,
# look for a POST request to https://api.7-eleven.com/auth/token, and extract
# the JSON from the outgoing request body.
ANON_CLIENT_CREDENTIALS = {
    "client_id": "sl3rgdU5c5ZvsYj95FGIuexau5Nt7J5OTf7VRPfV",
    "client_secret": "11BBlWqIeLenwAmPOKqz8WN5NIZRCCSBSEcBtp9DikLh90WL217OlaCvghuDJucGP5wG12VW2vQ7FRAzUMcYtOOrLtcd4eMqShsOJJKZnJOL5snAnih0uyUN8ZEURXPh",
    "grant_type": "client_credentials",
}


HEADERS = {
    # This seems to be a base64-encoded hash generated from a combination of data
    # in the above headers. Changing the trip ID or any of the other headers will
    # cause the API requests to fail validation.
    #
    # I'm not sure if this hash uses any time-based components to cause it to expire
    # over time or if it only maintain ingegrety between the other headers.
    #
    # These values were pulled from the token request in a private window (see above)
    "X-SEI-TRIP-ID": "OWMwYTY1NjE4OGExZWMwZDM2MDEzMDYwZGYzNWQ4OGM=",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15",
    "X-SEI-TZ": "-07:00",
    "X-SEI-VERSION": "3.6.0",
    "X-SEI-PLATFORM": "us_web",
}


class SevenElevenSpider(scrapy.Spider):
    name = "seven_eleven"
    allowed_domains = ["7-eleven.com"]

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://api.7-eleven.com/auth/token",
            method="POST",
            headers=HEADERS,
            data=ANON_CLIENT_CREDENTIALS,
            callback=self.fetch_stores,
        )

    def fetch_stores(self, response):
        auth = response.json()
        HEADERS.update({"Authorization": "Bearer cvrL4po6pXlnjzd7lrQRQ3iAbzDf9L"})

        yield scrapy.Request(
            "https://api.7-eleven.com/v4/stores/?lat=40.72786721004897&lon=-73.96717732880859&features=&radius=100000&limit=500&curr_lat=40.72786721004897&curr_lon=-73.96717732880859",
            headers=HEADERS,
        )

    def parse(self, response):
        data = response.json()

        for store in data["results"]:
            features = store["features"]

            if store["open_time"] == "24h" or (
                store["hours"]
                and store["hours"]["message"]
                and "24/7" in store["hours"]["message"]
            ):
                store_hours = "24/7"
            elif store["hours"] and store["hours"]["operating"]:
                no_minutes = re.compile(r"^\d+(a|p)m$")
                opening_hours = OpeningHours()

                for hours in store["hours"]["operating"]:
                    times = hours["detail"].split(" - ")
                    if len(times) < 2:
                        continue

                    (open_time, close_time) = times

                    if no_minutes.match(open_time):
                        open_time = f"{open_time[:-2]}:00{open_time[-2:]}"

                    if no_minutes.match(close_time):
                        close_time = f"{close_time[:-2]}:00{close_time[-2:]}"

                    opening_hours.add_range(
                        day=hours["key"][0:2],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%I:%M%p",
                    )

                store_hours = opening_hours.as_opening_hours()
            else:
                store_hours = None

            properties = {
                "ref": store["id"],
                "name": store["name"],
                "opening_hours": store_hours,
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "lon": float(store["lon"]),
                "lat": float(store["lat"]),
                "phone": store["phone"],
                "website": store["seo_web_url"],
                "extras": {
                    "shop": "convenience",
                    "amenity:fuel": "gas" in features,
                    "atm": "atm" in features,
                    "car_wash": "carwash" in features,
                    "fuel:diesel": "diesel" in features,
                    "fuel:propane": "propane" in features,
                },
            }

            yield GeojsonPointItem(**properties)

        next_url = data["next"]
        if next_url is not None:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(url=next_url, headers=HEADERS, callback=self.parse)
