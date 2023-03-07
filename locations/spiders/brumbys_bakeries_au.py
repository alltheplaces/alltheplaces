import json
import re

import chompjs
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
        if m := re.search(r"var storesObj =\s*({.+});\s*var", data_raw):
            stores = json.loads(chompjs.parse_js_object(m.group(1))["stores"])
            for store in stores:
                store["phone"] = store["phone"].split("tel:", 1)[1].split('"', 1)[0]
                item = DictParser.parse(store)
                item["lat"] = store["address"]["lat"]
                item["lon"] = store["address"]["lng"]
                item["addr_full"] = store["address"]["address"]
                yield scrapy.Request(url=item["website"], callback=self.parse_hours, meta={"item": item})

    def parse_hours(self, response):
        item = response.meta["item"]
        hours_raw = (
            " ".join(
                (
                    " ".join(
                        response.xpath(
                            '//h3[contains(@class, "heading-hours")]/following::table/tbody/tr/td/text()'
                        ).getall()
                    )
                ).split()
            )
            .upper()
            .replace("24 HOURS", "Mon - Sun 12:00 AM - 11:59 PM")
        )
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_raw)
        item["opening_hours"] = oh.as_opening_hours()
        yield item
