import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CornerBakeryCafeSpider(StructuredDataSpider):
    name = "corner_bakery_cafe"
    item_attributes = {"brand": "Corner Bakery Cafe", "brand_wikidata": "Q5171598"}
    allowed_domains = ["cornerbakerycafe.com"]
    start_urls = [
        "https://cornerbakerycafe.com/locations/all",
    ]

    def parse(self, response):
        place_urls = response.xpath('//*[@class="loc-icon-home"]/a[1]/@href').extract()
        for path in place_urls:
            yield scrapy.Request(
                url=response.urljoin(path),
                callback=self.parse_sd,
            )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            days, times = hour.split(" ")
            open_hour, close_hour = times.split("-")
            if len(days) > 2:
                day = days.split(",")
                for d in day:
                    opening_hours.add_range(
                        day=d,
                        open_time=open_hour,
                        close_time=close_hour,
                        time_format="%H:%M",
                    )
            else:
                opening_hours.add_range(
                    day=days,
                    open_time=open_hour,
                    close_time=close_hour,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def post_process_item(self, item, response, ld_data):
        item["ref"] = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        try:
            hours = self.parse_hours(ld_data["openingHours"])
            if hours:
                item["opening_hours"] = hours
        except:
            pass

        yield item