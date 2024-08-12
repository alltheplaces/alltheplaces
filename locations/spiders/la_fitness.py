import datetime
import re

import scrapy
from scrapy import Selector
from scrapy.http import JsonRequest

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class LaFitnessSpider(scrapy.Spider):
    name = "la_fitness"
    item_attributes = {"brand": "LA Fitness", "brand_wikidata": "Q6457180"}
    allowed_domains = ["lafitness.com"]
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://lafitness.com/Pages/GetClubLocations.aspx/GetClubLocation",
            method="POST",
        )

    def parse_hours(self, elems: Selector) -> OpeningHours:
        opening_hours = OpeningHours()

        hours = elems.xpath(".//text()").extract()

        if not hours:
            return None

        hours.pop(hours.index("CLUB HOURS"))

        hours = list(zip(hours[0::2], hours[1::2]))
        for hour in hours:
            if (hour[0] == "Mon - Sun") & (hour[1] == "24 Hours Open"):
                return "24/7"

            try:
                open_time, close_time = re.search(r"(.*)\s-\s(.*)", hour[1], re.IGNORECASE).groups()
            except:
                if hour[1] == "24 Hours Open":
                    open_time, close_time = "12:00am", "11:59pm"
                else:
                    raise
            if close_time == "Midnight":
                close_time = "12:00am"
            if open_time == "Midnight":
                open_time = "12:00am"

            open_time = datetime.datetime.strptime(open_time, "%I:%M%p").strftime("%H:%M")
            close_time = datetime.datetime.strptime(close_time, "%I:%M%p").strftime("%H:%M")

            if days := re.search(r"([a-z]{3})\s-\s([a-z]{3})", hour[0], re.IGNORECASE):
                day_start, day_end = days.groups()
                opening_hours.add_days_range(
                    day_range(sanitise_day(day_start), sanitise_day(day_end)), open_time, close_time
                )
            else:
                opening_hours.add_range(sanitise_day(hour[0]), open_time, close_time)

        return opening_hours

    def parse_club(self, response):
        properties = response.meta["properties"]

        properties.update(
            {
                "phone": response.xpath('//span[contains(@id, "lblClubPhone")]/text()').extract_first(),
                "street_address": response.xpath('//span[contains(@id, "lblClubAddress")]/text()').extract_first(),
                "postcode": response.xpath('//span[contains(@id, "lblZipCode")]/text()').extract_first(),
                "website": response.url,
                "opening_hours": self.parse_hours(response.xpath('//div[@id="divClubHourPanel"]//tr')),
            }
        )

        yield Feature(**properties)

    def parse(self, response):
        locations = response.json()["d"]
        for location in locations:
            properties = {
                "name": location["Description"],
                "ref": location["ClubID"],
                "lat": float(location["Latitude"]),
                "lon": float(location["Longitude"]),
                "image": f'https://lafitness.com/Pages/Images/ClubExterior/{location["ClubID"]}.jpg',
                "addr_full": location["Address"].replace("<br />", ","),
                "city": location["City"],
                "state": location["State"],
            }

            yield scrapy.Request(
                "https://www.lafitness.com/pages/" + location["ClubHomeURL"],
                callback=self.parse_club,
                meta={"properties": properties},
            )
