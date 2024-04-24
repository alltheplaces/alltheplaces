import json
import re

import chompjs
import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day


class ToolstationSpider(scrapy.spiders.SitemapSpider):
    name = "toolstation"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    sitemap_urls = [
        "https://www.toolstation.com/sitemap/branches.xml",
        "https://www.toolstation.fr/sitemap/branches.xml",
        "https://www.toolstation.nl/sitemap/branches.xml",
    ]
    gm_pattern = re.compile(r"var store = (.*?)\n", re.MULTILINE | re.DOTALL)
    params_pattern = re.compile(r"function\(([_$\w,\s]+)\)")
    values_pattern = re.compile(r"}\((.+)\)\);")
    stores_pattern = re.compile(r"data:(\[.+\]),fe")

    def parse(self, response):
        if js := response.xpath('//script[contains(., "var store")]/text()').get():
            store = json.loads(re.search(self.gm_pattern, js).group(1))[0]
            item = DictParser.parse(store)
            item["website"] = response.url
            item["addr_full"] = store["address_text"].split("<br /><br />")[0]
            yield item
        elif js := response.xpath('//script[contains(text(), "__NUXT__")]/text()').get():
            # stores is actually a JS function, so we have to parse the parameters and values
            params = re.search(self.params_pattern, js).group(1).split(",")
            values = chompjs.parse_js_object("[" + re.search(self.values_pattern, js).group(1) + "]")
            args = {}
            for i in range(0, len(params)):
                args[params[i]] = values[i]

            store = chompjs.parse_js_object(re.search(self.stores_pattern, js).group(1))[0]["branch"]
            self.populate(store, args)

            if store["status"] != 1:
                return

            item = DictParser.parse(store)
            item["website"] = response.url
            item["addr_full"] = store["address_text"]

            item["opening_hours"] = OpeningHours()
            for rule in store["opening_hours"]:
                days, times = rule.split(": ", 1)
                if "-" in days:
                    start_day, end_day = days.split("-")
                else:
                    start_day = end_day = days
                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
                if start_day and end_day:
                    start_time, end_time = times.strip().split("-")
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day), start_time, end_time, time_format="%H%M"
                    )

            yield item

    @staticmethod
    def populate(data: dict, args: dict):
        for key, value in data.items():
            if isinstance(value, str):
                if value in args:
                    data[key] = args[value]
            elif isinstance(value, list):
                for i, x in enumerate(value):
                    if isinstance(x, dict):
                        ToolstationSpider.populate(x, args)
                    elif x in args:
                        value[i] = args[x]
            elif isinstance(value, dict):
                ToolstationSpider.populate(value, args)
