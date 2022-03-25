# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class BoneFishGrillSpider(scrapy.Spider):
    download_delay = 0.2
    name = "bonefishgrill"
    allowed_domains = ["bonefishgrill.com"]
    start_urls = ("https://www.bonefishgrill.com/locations/all",)

    def parse(self, response):
        urls = response.xpath('//li[@class="location-row"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = response.xpath(
            '//script[contains(text(), "initLocationDetail")][1]/text()'
        ).extract_first()

        try:
            properties = {
                "ref": re.search(r'"UnitId":"(.*?)"', data).group(1),
                "name": re.search(r'"City":"(.*?)"', data).group(1),
                "addr_full": re.search(r'"Address":"(.*?)"', data).group(1),
                "city": re.search(r'"City":"(.*?)"', data).group(1),
                "state": re.search(r'"State":"(.*?)"', data).group(1),
                "postcode": re.search(r'"Zip":"(.*?)"', data).group(1),
                "phone": re.search(r'"Phone":"(.*?)"', data).group(1),
                "lat": re.search(r'"Latitude":"(.*?)"', data).group(1),
                "lon": re.search(r'"Longitude":"(.*?)"', data).group(1),
                "website": response.url,
            }

            hours = self.parse_hours(re.search(r'"Hours":(.*?})', data).group(1))

            if hours:
                properties["opening_hours"] = hours
            yield GeojsonPointItem(**properties)
        except:
            pass

    def parse_hours(self, response):
        opening_hours = OpeningHours()
        weekdays = response
        hrs = json.loads(weekdays)
        WEEKDAYS = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for DAY in WEEKDAYS:
            open = hrs.get(DAY + "Open")
            close = hrs.get(DAY + "Close")

            opening_hours.add_range(
                day=DAY_MAPPING[DAY],
                open_time=open,
                close_time=close,
                time_format="%H:%M %p",
            )

        return opening_hours.as_opening_hours()
