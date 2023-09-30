import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class CornerBakeryCafeSpider(scrapy.Spider):
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
                callback=self.parse_store,
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

    def parse_store(self, response):
        data = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').extract_first().replace("\r\n", "")
        )

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": data["name"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "phone": data["telephone"],
            "website": data["url"],
        }

        try:
            hours = self.parse_hours(data["openingHours"])
            if hours:
                properties["opening_hours"] = hours
        except:
            pass

        yield Feature(**properties)
