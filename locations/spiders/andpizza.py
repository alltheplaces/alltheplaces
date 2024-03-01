from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class AndPizzaSpider(Spider):
    name = "andpizza"
    item_attributes = {"brand": "&pizza", "brand_wikidata": "Q21189222"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.andpizza.com/webapi/v100/partners/shops",
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjIsInBhcnRuZXIiOiJpNzIiLCJpc3MiOiJodHRwczovL2FwaS5hbmRwaXp6YS5jb20iLCJpYXQiOjE1OTgyOTEwNzUsImV4cCI6MTkxMzY1MTA3NSwibmJmIjoxNTk4MjkxMDc1LCJqdGkiOiI4VWh1VnhJRjFwZFhrSXplIn0.rXJL4rt5YbT4XRk21sSrkoGffJ5ttowV3UbHInZcnMs",
            },
        )

    @staticmethod
    def parse_hours(rules: [dict]) -> OpeningHours:
        oh = OpeningHours()

        for rule in rules:
            if "-" in rule["label"]:
                start_day, end_day = rule["label"].split("-")
            else:
                start_day = end_day = rule["label"]
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day) or start_day
            if start_day:
                start_time, end_time = rule["value"].split(" - ")
                oh.add_days_range(day_range(start_day, end_day), start_time, end_time, time_format="%I:%M %p")

        return oh

    def parse(self, response):
        for location in response.json()["data"]:
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            item["opening_hours"] = self.parse_hours(location["service_schedule"]["general"])

            yield item
