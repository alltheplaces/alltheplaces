import csv
import datetime

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.searchable_points import open_searchable_points

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class MarshallsSpider(scrapy.Spider):
    name = "marshalls"
    allowed_domains = ["tjx.com"]

    chains = {
        "08": ["TJ Maxx", "Q10860683"],
        "10": ["Marshalls", "Q15903261"],
        "28": ["Homegoods", "Q5887941"],
        "29": ["Homesense", "Q16844433"],
        "50": ["Sierra" "Q7511598"],
    }

    def start_requests(self):
        url = "https://marketingsl.tjx.com/storelocator/GetSearchResults"
        payload = {"chain": "10", "lang": "en", "maxstores": "100"}

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            reader = csv.DictReader(points)
            for point in reader:
                payload.update({"geolat": point["latitude"], "geolong": point["longitude"]})

                yield scrapy.http.FormRequest(
                    url=url,
                    method="POST",
                    formdata=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                )

    def parse_hours(self, hours):
        try:
            """Mon-Thu: 9am - 9pm, Black Friday: 8am - 10pm, Sat: 9am - 9pm, Sun: 10am - 8pm"""
            opening_hours = OpeningHours()
            hours = hours.replace("Black Friday", "Fri")

            for x in hours.split(","):
                days, hrs = x.split(":", 1)
                try:
                    open_time, close_time = hrs.split("-")
                except:
                    continue

                if ":" in open_time:
                    open_time = datetime.datetime.strptime(open_time.strip(), "%I:%M%p").strftime("%H:%M")
                else:
                    open_time = datetime.datetime.strptime(open_time.strip(), "%I%p").strftime("%H:%M")

                if ":" in close_time:
                    close_time = datetime.datetime.strptime(close_time.strip(), "%I:%M%p").strftime("%H:%M")
                else:
                    close_time = datetime.datetime.strptime(close_time.strip(), "%I%p").strftime("%H:%M")

                if "-" in days:
                    start_day, end_day = days.split("-")
                    for day in DAYS[DAYS.index(start_day.strip()) : DAYS.index(end_day.strip()) + 1]:
                        opening_hours.add_range(day[:2], open_time=open_time, close_time=close_time)

                else:
                    day = days.strip()[:2]
                    opening_hours.add_range(day, open_time=open_time, close_time=close_time)

            return opening_hours.as_opening_hours()
        except:
            pass

    def parse(self, response):
        data = response.json()

        for store in data["Stores"]:
            item = DictParser.parse(store)
            item["brand"], item["brand_wikidata"] = self.chains.get(store["Chain"])
            hours = self.parse_hours(store["Hours"])
            if hours:
                item["opening_hours"] = hours

            yield item
