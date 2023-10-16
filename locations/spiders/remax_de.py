import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RemaxDeSpider(scrapy.Spider):
    name = "remax_de"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.com", "wp.ooremax.com"]
    per_page = 24
    start_urls = [f"https://wp.ooremax.com/wp-json/eapi/v1/agencies?per_page={per_page}&page=1"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data.get("acf"))
            item["ref"] = data.get("id")
            open_hours = (
                data.get("yoast_head_json", {}).get("schema", {}).get("@graph", {})[3].get("openingHoursSpecification")
            )
            oh = OpeningHours()
            for days in open_hours:
                for day in days.get("dayOfWeek"):
                    oh.add_range(
                        day=day,
                        open_time=days.get("opens"),
                        close_time=days.get("closes"),
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item

        page = int(re.findall(r"\d+$", response.url)[0]) + 1
        if len(response.json()):
            url = f"https://wp.ooremax.com/wp-json/eapi/v1/agencies?per_page={self.per_page}&page={page}"
            yield scrapy.Request(url=url, callback=self.parse)
