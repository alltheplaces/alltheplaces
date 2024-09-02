from datetime import datetime
from zoneinfo import ZoneInfo

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MilliesGBSpider(Spider):
    name = "millies_gb"
    item_attributes = {"brand": "Millie's", "brand_wikidata": "Q1935533"}
    allowed_domains = ["www.milliescookies.com"]
    start_urls = ["https://www.milliescookies.com/api/n/bundle?requests=[{%22type%22:%22store%22,%22filter%22:{},%22verbosity%22:1,%22action%22:%22find%22,%22children%22:[{%22_reqId%22:0}]}]"]

    def parse(self, response):
        for location in response.json()["catalog"]:
            item = DictParser.parse(location)
            item.pop("website")

            # Opening hours parsing is difficult because the next 3
            # months of opening times on each day is provided. Some
            # of these opening times are public holidays and thus are
            # special hours to be ignored. Thus we need to loop
            # through the 3 months of opening times, ignoring any
            # public holidays and using the next normal opening times
            # for each day of the week (London time).
            item["opening_hours"] = OpeningHours()
            gb_timezone = ZoneInfo("Europe/London")
            opening_hours = {}
            for date, day_hours in location["days"].items():
                if not day_hours["status"] or day_hours["holiday"] or day_hours["special_day"]:
                    continue
                day_name = datetime.fromisoformat(date).astimezone(gb_timezone).strftime("%A")
                if day_name in opening_hours.keys():
                    continue
                if day_hours["open_break"] == day_hours["close_break"]:
                    opening_hours[day_name] = [(day_hours["open"], day_hours["close"])]
                else:
                    opening_hours[day_name] = [
                        (day_hours["open"], day_hours["open_break"]),
                        (day_hours["close_break"], day_hours["close"]),
                    ]
            for day_name, day_hours in opening_hours.items():
                for day_hours_period in day_hours:
                    item["opening_hours"].add_range(day_name, day_hours_period[0], day_hours_period[1])

            yield item
