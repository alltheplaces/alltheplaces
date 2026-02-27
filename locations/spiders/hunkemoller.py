import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class HunkemollerSpider(SitemapSpider):
    name = "hunkemoller"
    item_attributes = {"brand": "Hunkemöller", "brand_wikidata": "Q2604175"}
    sitemap_urls = ["https://www.hunkemoller.be/nl/sitemap-stores.xml"]
    sitemap_rules = [
        (
            r"https://www.hunkemoller.be/nl/winkel/.+/.+$",
            "parse",
        ),
    ]

    def parse(self, response, **kwargs):
        script_text = json.loads(
            re.search(
                r"data\"s*:\s*\[({\"address1\".*})\],\s*\"total",
                response.xpath('//*[contains(text(), "latitude")]/text()').get(),
            ).group(1)
        )

        item = DictParser.parse(script_text)
        item["website"] = response.url

        oh = OpeningHours()
        for day_time in script_text.get("c_openingHours") or []:
            day = sanitise_day(day_time["dayOfWeek"], DAYS_NL)
            open_time = day_time["open"]
            close_time = day_time["close"]
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh

        yield item
