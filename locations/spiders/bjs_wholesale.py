import json
import re
from datetime import datetime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

DAY_MAPPING = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class BjsWholesaleSpider(SitemapSpider):
    name = "bjs_wholesale"
    item_attributes = {"brand": "BJ's Wholesale Club", "brand_wikidata": "Q4835754"}
    allowed_domains = ["bjs.com"]
    sitemap_urls = ["https://www.bjs.com/bjs_ancillary_sitemap.xml"]
    sitemap_rules = [(r"/cl/[-\w]+/\d+", "parse_store")]

    def parse_hours(self, hours: list):
        opening_hours = OpeningHours()

        if hours:
            hours = hours[0].get("value").split("<br>") or []
            for hour in hours:
                try:
                    day, open_time, close_time = re.search(r"(.*?):\s(.*?)\s-\s(.*?)$", hour).groups()
                except AttributeError:  # closed
                    continue
                open_time = (
                    datetime.strptime(open_time, "%I:%M %p")
                    if ":" in open_time
                    else datetime.strptime(open_time, "%I %p")
                ).strftime("%H:%M")
                close_time = (
                    datetime.strptime(close_time, "%I:%M %p")
                    if ":" in close_time
                    else datetime.strptime(close_time, "%I %p")
                ).strftime("%H:%M")

                if "-" in day:
                    start_day, end_day = day.split("-")
                    start_day = start_day.strip()
                    end_day = end_day.strip()
                    for d in DAY_MAPPING[DAY_MAPPING.index(start_day[:2]) : DAY_MAPPING.index(end_day[:2]) + 1]:
                        opening_hours.add_range(
                            day=d,
                            open_time=open_time,
                            close_time=close_time,
                            time_format="%H:%M",
                        )
        return opening_hours.as_opening_hours()

    def parse_store(self, response: Response) -> Any:
        store = {}
        json_blob = json.loads(
            response.xpath('//script[@id="bjs-universal-app-state"]/text()')
            .get("")
            .replace("&q;", '"')
            .replace("&s;", "'")
            .replace("&a;", "&")
            .replace("&l;", "<")
            .replace("&g;", ">")
        )
        for key in json_blob:
            if "club/search" in key:
                store = json_blob[key]["Stores"]["PhysicalStore"][0]
                break
        store["ref"] = store.pop("storeName")
        item = DictParser.parse(store)
        item["branch"] = store["Description"][0]["displayStoreName"]
        item["website"] = response.url
        hours = self.parse_hours([attr for attr in store["Attribute"] if attr["name"] == "Hours of Operation"])
        if hours:
            store["opening_hours"] = hours

        apply_category(Categories.SHOP_WHOLESALE, item)

        yield item
