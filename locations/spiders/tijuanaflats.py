import json
import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TijuanaFlatsSpider(scrapy.Spider):
    name = "tijuanaflats"
    item_attributes = {"brand": "Tijuana Flats", "brand_wikidata": "Q7801833"}
    allowed_domains = ["tijuanaflats.com"]
    start_urls = ("https://www.tijuanaflats.com/locations",)

    def parse(self, response):
        data = json.loads(response.xpath('//tjs-view-locations/attribute::*[name()=":locations"]').extract_first())
        for row in data:
            for ent in row["yoast_json_ld"][0]["@graph"]:
                if ent["@type"] == "WebPage" and row["slug"] in ent["url"]:
                    name = ent["name"]

            properties = {
                "ref": row["slug"],
                "name": name,
                "lat": row["acf"]["physical_location"]["lat"],
                "lon": row["acf"]["physical_location"]["lng"],
                "street_address": clean_address([row["acf"]["address_1"], row["acf"]["address_2"]]),
                "city": row["acf"]["city"],
                "state": row["acf"]["state"],
                "postcode": row["acf"]["zip"],
                "phone": row["acf"]["contact_phone"],
                "website": f'https://www.tijuanaflats.com/locations/{row["slug"]}',
                "opening_hours": self.parse_opening_hours(row["acf"]["hours_of_operation"]),
            }
            yield Feature(**properties)

    @staticmethod
    def parse_opening_hours(rules: str) -> OpeningHours:
        oh = OpeningHours()
        for start_day, end_day, start_hours, start_mins, start_zone, end_hours, end_mins, end_zone in re.findall(
            r"(\w+)(?:\s*-\s*(\w+))?:? (\d+)(:\d+)? (AM|PM) - (\d+)(:\d+)? (AM|PM)", rules
        ):
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day) or start_day
            if start_day and end_day:
                start_time = f'{start_hours}{start_mins or ":00"} {start_zone}'
                end_time = f'{end_hours}{end_mins or ":00"} {end_zone}'
                oh.add_days_range(day_range(start_day, end_day), start_time, end_time, time_format="%I:%M %p")
        return oh
