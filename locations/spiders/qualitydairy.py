# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

URL = "qualitydairy.com"


class QuiznosSpider(scrapy.Spider):
    name = "qualitydiary"
    item_attributes = {"brand": "Quality Dairy", "brand_wikidata": "Q23461886"}
    allowed_domains = [URL]
    start_urls = ("http://qualitydairy.com/v15/stores/",)

    def normalize_time(self, time_str):
        match = re.search(r"(.*)(am|pm| a.m| p.m)", time_str)
        h, am_pm = match.groups()
        h = h.split(":")

        return "%02d:%02d" % (
            int(h[0]) + 12 if am_pm == " p.m" or am_pm == "pm" else int(h[0]),
            int(h[1]) if len(h) > 1 else 0,
        )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None

        for day_info in store_hours:
            date_values = day_info.xpath(".//td")
            date_values[0] = re.search(
                "<td>(.*?)</td>", date_values[0].extract()
            ).group(1)
            date_values[1] = re.search(
                "<td>(.*?)</td>", date_values[1].extract()
            ).group(1)
            date_values[3] = re.search(
                "<td>(.*?)</td>", date_values[3].extract()
            ).group(1)

            day = date_values[0][:2].title()

            if date_values[1] == "" or date_values[3] == "":
                return None

            day_open = self.normalize_time(date_values[1])
            day_close = self.normalize_time(date_values[3])
            hours = day_open + "-" + day_close

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        data = response.text
        stores = json.loads(re.search("qd_locations = (.*);", data).group(1))

        for store in stores:

            props = {
                "lat": store.get("lat"),
                "lon": store.get("lng"),
                "ref": str(store.get("id")),
                "phone": store.get("phone"),
                "name": store.get("name"),
                "addr_full": store.get("address1"),
                "city": store.get("city"),
                "state": store.get("state"),
                "postcode": "",
                "website": store.get("url"),
            }

            yield scrapy.Request(
                store.get("url"),
                meta={"product": props},
                callback=self.parse_detail_product,
            )

    def parse_detail_product(self, response):
        product = response.meta.get("product")
        open_dates = response.xpath('//table[@id="hours-table"]//tr')
        product["opening_hours"] = (
            self.store_hours(open_dates) if len(open_dates) > 0 else "24/7"
        )

        yield GeojsonPointItem(**product)
