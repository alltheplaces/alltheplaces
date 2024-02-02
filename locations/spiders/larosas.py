import re

import scrapy

from locations.items import Feature

hour_label = ["Mo-Th", "Fr", "Sa", "Su"]


class LarosasSpider(scrapy.Spider):
    name = "larosas"
    item_attributes = {"brand": "Larosa's", "brand_wikidata": "Q6460833"}
    allowed_domains = ["www.larosas.com"]
    start_urls = ("https://www.larosas.com/pizzeria.aspx",)

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2}) ([ap.m]{2})", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2}) ([ap.m]{2})", time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p." else int(h),
            int(m),
        )

    def store_hours(self, store_hours):
        opening_hours = ""
        hours = []
        mon_thurs = store_hours.xpath("@diningMonThurs").extract_first()
        fri = store_hours.xpath("@diningFri").extract_first()
        sat = store_hours.xpath("@diningSat").extract_first()
        sun = store_hours.xpath("@diningSun").extract_first()

        hours.append(mon_thurs)
        hours.append(fri)
        hours.append(sat)
        hours.append(sun)

        index = 0

        for hour in hours:
            """
            # detect store which has full time service
            """
            if not hour:
                return "24/7"

            if "iii" in hour:
                return "24/7"

            if "xxx" in hour:
                return "24/7"

            """
                # Replace all unexpected type to expected type for regex.
            """
            if "Midnight" in hour:
                hour = hour.replace("Midnight", "12 a.m")

            if "Noon" in hour:
                hour = hour.replace("Noon", "12:00 p.m")

            if "12 Noon" in hour:
                hour = hour.replace("12 Noon", "12 p.m")

            if "12 noon" in hour:
                hour = hour.replace("12 noon", "12 p.m")

            tmp = hour.split("-")
            day_open = tmp[0].strip()
            day_close = tmp[1].strip()

            day_open = self.normalize_time(day_open)
            day_close = self.normalize_time(day_close)

            if opening_hours:
                opening_hours += ","

            opening_hours += hour_label[index] + " " + day_open + "-" + day_close
            index += 1

        return opening_hours

    def parse(self, response):
        data = response.xpath(".//marker")
        for item in data:
            properties = {
                "name": item.xpath("@storeName").extract()[0],
                "city": item.xpath("@city").extract()[0],
                "ref": item.xpath("@num").extract()[0],
                "lon": item.xpath("@long").extract()[0],
                "lat": item.xpath("@lat").extract()[0],
                "addr_full": item.xpath("@storeAddress").extract()[0],
                "phone": item.xpath("@phone").extract()[0],
                "state": item.xpath("@state").extract()[0],
                "postcode": item.xpath("@zip").extract()[0],
                "website": item.xpath("@applyNowLink").extract()[0],
            }

            opening_hours = self.store_hours(item)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield Feature(**properties)
