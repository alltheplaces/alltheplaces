import re

import geonamescache
import scrapy
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Sunday": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}


class FirehouseSubsSpider(scrapy.Spider):
    name = "firehouse_subs"
    item_attributes = {"brand": "Firehouse Subs", "brand_wikidata": "Q5451873"}
    allowed_domains = ["firehousesubs.com"]

    def start_requests(self):
        for state in geonamescache.GeonamesCache().get_us_states().keys() | ["PR"]:
            yield JsonRequest(url=f"https://www.firehousesubs.com/FindLocations/GetLocationsByState/?state={state}")

    def parse(self, response):
        for store_json_data in response.json():
            addr_full = None
            address = store_json_data.get("address")
            address2 = store_json_data.get("address2")
            if address:
                addr_full = address
            if address2:
                addr_full += f", {address2}"

            store_page_url = store_json_data.get("moreInfoUrl")

            properties = {
                # 'siteId' appears to be the publicly facing store number.  I would prefer to use it, but
                # it comes back as null for some stores.  'id' also appears in the data, reliably.
                # So use it instead.
                "ref": store_json_data.get("id"),
                "name": store_json_data.get("title"),
                "street_address": addr_full,
                "city": store_json_data.get("city"),
                "state": store_json_data.get("state"),
                "postcode": store_json_data.get("zip"),
                "phone": store_json_data.get("phone"),
                "website": store_page_url,
                "lon": store_json_data.get("longitude"),
                "lat": store_json_data.get("latitude"),
            }

            # The JSON has today's hours, but we have to visit the store page
            # to find hours for every day of the week.
            if store_page_url:
                yield scrapy.http.Request(
                    url=store_page_url,
                    method="GET",
                    callback=self.add_hours,
                    cb_kwargs={"properties": properties},
                )
            else:
                yield Feature(**properties)

    def add_hours(self, response, properties):
        opening_hours = OpeningHours()

        # Hours are listed in markup as a series of list items, one for each
        # day of the week.
        li_hours = response.xpath('//div[@class="hours"]//ol//li')

        for li in li_hours:
            day = li.xpath('./span[@class="day"]/text()').get()
            times = li.xpath('./span[@class="time"]/text()').get()
            # "Coming Soon" stores may not have times listed yet
            if not times:
                continue

            # Times for each day listed in a format like this:  10:30am - 9:00pm
            # Note:
            # - Whitespace is inconsistent
            # - Some stores may have extra information after; e.g., "10:30am - 9:00pm (drive-thru opens 9:30)"
            regex = re.compile(r"^\s*(\d{1,2}:\d{2}\s*[a|p]m)\s*-\s*(\d{1,2}:\d{2}\s*[a|p]m)")
            match = re.search(regex, times)
            if not match or len(match.groups()) != 2:
                continue

            open_time = match.group(1)
            close_time = match.group(2)

            # Across pages, we see inconsistent whitespace in the times. Remove it all.
            open_time = open_time.replace(" ", "")
            close_time = close_time.replace(" ", "")

            opening_hours.add_range(DAY_MAPPING[day], open_time, close_time, time_format="%I:%M%p")

        properties["opening_hours"] = opening_hours.as_opening_hours()
        yield Feature(**properties)
