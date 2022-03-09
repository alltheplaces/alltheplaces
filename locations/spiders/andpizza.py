# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class TacocabanaSpider(scrapy.Spider):
    name = "andpizza"
    item_attributes = {"brand": "&pizza"}
    allowed_domains = ["andpizza.com"]
    start_urls = ("https://andpizza.com",)

    def normalize_time(sef, time_str):
        match = re.search(r"([0-9]{1,2}) (a|p)m$", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2})(a|p)m$", time_str)
            h, am_pm = match.groups()
        else:
            h, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p." else int(h),
            int("0"),
        )
        return ""

    def hours(self, data):
        opening_hours = ""

        if "&bar" in data:
            data = data[: data.index("&bar")]

        for i in range(len(data) // 2):
            days = data[i * 2].split(" ")
            hours = data[i * 2 + 1]
            if len(days) == 1:
                day = days[0][:2]
            elif len(days) == 3:
                day = days[0][:2] + "-" + days[2][:2]
            else:
                day = "Mo-Su"

            hours = hours.split("-")
            open = self.normalize_time(hours[0].strip())
            close = self.normalize_time(hours[1].strip())

            open_close = "{}-{}".format(open, close)

            opening_hours += "{} {}; ".format(day, open_close)

        return opening_hours

    def parse(self, response):
        selector = scrapy.Selector(response)
        stores = selector.css("div.location")

        for store in stores:
            ref = store.css("div.location::attr(class)").extract_first().split(" ")[1]
            name = store.css("a.knockout *::text").extract_first()
            address = store.css("address>a *::text").extract()
            address1 = address[0]
            address2 = address[len(address) - 1].split(",")
            hours = store.css("div.hours")

            store_hours = ""
            if not hours.css("span>a"):
                store_hours = self.hours(store.css("div.hours *::text").extract())

            properties = {
                "ref": ref,
                "name": name,
                "street": address1,
                "city": address2[0],
                "state": address2[1].split(" ")[1],
                "postcode": address2[1].split(" ")[2],
                "opening_hours": store_hours,
            }

            yield GeojsonPointItem(**properties)
