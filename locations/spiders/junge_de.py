import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_DE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class JungeDESpider(Spider):
    name = "junge_de"
    item_attributes = {"brand": "Junge", "brand_wikidata": "Q1561751"}

    async def start(self):
        yield scrapy.Request(url="https://shop.jb.de/Catalog/GetStoresCore", method="POST", callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//ul//li"):
            item = Feature()
            item["branch"] = location.xpath(".//h3/text()").get()
            item["ref"] = location.xpath(".//@data-storeid").get()
            item["street_address"] = location.xpath(".//p/text()").get()
            item["addr_full"] = merge_address_lines([item["street_address"], location.xpath(".//p[2]/text()").get()])
            item["lon"], item["lat"] = re.search(
                r"clickStore\((\d+\.\d+)\s*,\s*(\d+\.\d+)", location.xpath(".//@onclick").get()
            ).groups()
            oh = OpeningHours()
            for day_time in location.xpath(
                './/p[normalize-space()="Öffnungszeiten"]/following::table[1]/tr[position() <= 2]'
            ):
                day = day_time.xpath(".//td").xpath("normalize-space()").get()
                time = day_time.xpath(".//td[2]").xpath("normalize-space()").get()

                if "-" in day:
                    start_day, end_day = day.split("-")
                    start_day = sanitise_day(start_day, DAYS_DE)
                    end_day = sanitise_day(end_day, DAYS_DE)
                else:
                    start_day = sanitise_day(day, DAYS_DE)
                    end_day = start_day
                if start_day and end_day:
                    if time == "geschlossen":
                        oh.set_closed(day_range(start_day, end_day))
                    else:
                        open_time, close_time = time.split("-")
                        oh.add_days_range(day_range(start_day, end_day), open_time, close_time)
            item["opening_hours"] = oh
            yield item
