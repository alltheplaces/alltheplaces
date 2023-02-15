import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BrumbysBakeriesAUSpider(scrapy.Spider):
    name = "brumbys_bakeries_au"
    item_attributes = {"brand": "Brumby's Bakeries", "brand_wikidata": "Q4978794"}
    allowed_domains = ["www.brumbys.com.au"]
    start_urls = ["https://www.brumbys.com.au/store-locator/"]

    def parse(self, response):
        data_raw = response.xpath('//script[@id="theme_app_js-js-extra"]/text()').get()
        data_clean = (
            data_raw.split("var storesObj = ", 1)[1]
            .split(";\n", 1)[0]
            .replace('\\"', '"')
            .replace("\\\\\\", "".replace("\\/", "/"))
            .replace('\\\\"', '\\"')
            .replace(':"[', ":[")
            .replace(']","', '],"')
            .replace("\\\\u2019", "'")
            .replace("\\\\u00a0", "")
        )
        stores = json.loads(data_clean)["stores"]
        for store in stores:
            store["phone"] = store["phone"].split("tel:", 1)[1].split('"', 1)[0]
            item = DictParser.parse(store)
            item["lat"] = store["address"]["lat"]
            item["lon"] = store["address"]["lng"]
            item["addr_full"] = store["address"]["address"]
            yield scrapy.Request(url=item["website"], callback=self.parse_hours, meta={"item": item})

    def parse_hours(self, response):
        item = response.meta["item"]
        hours_raw = response.xpath(
            '//h3[contains(@class, "heading-hours")]/following::table/tbody/tr/td/text()'
        ).getall()
        hours_raw = [hours_raw[n : n + 2] for n in range(0, len(hours_raw), 2)]
        hours_parsing_error = False
        oh = OpeningHours()
        for day_range_raw in hours_raw:
            if day_range_raw[0].strip().upper() == "24 HOURS":
                day_names_clean = "Mon - Sun"
                time_range_clean = "12:00 AM - 11:59 PM"
            else:
                day_names_clean = day_range_raw[0].strip().replace("–", "-").replace(":", "")
                time_range_clean = day_range_raw[1].strip().replace("–", "-")
            days = []
            match day_names_clean:
                case "Monday to Sunday" | "Monday - Sunday" | "Mon - Sun":
                    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                case "Monday to Friday" | "Monday - Friday" | "Mon - Fri" | "Weekdays" | "Monday, Tuesday, Wednesday, Thursday, Friday":
                    days = ["Mo", "Tu", "We", "Th", "Fr"]
                case "Saturday and Sunday" | "Saturday & Sunday" | "Sat - Sun" | "Weekends":
                    days = ["Sa", "Su"]
                case "Monday" | "Mon":
                    days = ["Mo"]
                case "Tuesday" | "Tue":
                    days = ["Tu"]
                case "Wednesday" | "Wed":
                    days = ["We"]
                case "Thursday" | "Thu":
                    days = ["Th"]
                case "Friday" | "Fri":
                    days = ["Fr"]
                case "Saturday" | "Sat":
                    days = ["Sa"]
                case "Sunday" | "Sun":
                    days = ["Su"]
                case "Christmas Day, Boxing Day, 1st Jan and 2nd Jan":
                    days = []
                case _:
                    hours_parsing_error = True
            if not hours_parsing_error:
                if "CLOSED" in time_range_clean:
                    continue
            for start_hour, start_min, start_am_pm, end_hour, end_min, end_am_pm in re.findall(
                r"(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)\s*-\s*(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)",
                time_range_clean,
                flags=re.IGNORECASE,
            ):
                if len(start_hour) == 1:
                    start_hour = "0" + start_hour
                if len(end_hour) == 1:
                    end_hour = "0" + end_hour
                if start_min == "":
                    start_min = "00"
                if end_min == "":
                    end_min = "00"
                start_time = f"{start_hour}:{start_min} {start_am_pm}"
                end_time = f"{end_hour}:{end_min} {end_am_pm}"
                for day in days:
                    oh.add_range(day, start_time, end_time, "%I:%M %p")
        if not hours_parsing_error:
            item["opening_hours"] = oh.as_opening_hours()
        yield item
