# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Pier1Spider(scrapy.Spider):
    name = "pier1"
    item_attributes = {"brand": "Pier 1"}
    allowed_domains = ["www.pier1.com"]
    start_urls = [
        "https://www.pier1.com/on/demandware.store/Sites-pier1_us-Site/default/LocalStore?",
    ]
    download_delay = 2  # Pier1's site struggles to keep up with faster downloads

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="store-info card hover z-depth-0"]/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+=(.+?)(?:\.html|$)", response.url).group(1)

        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), \
        "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": data["name"],
            "ref": ref,
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url
            # Store coordinates not present on store pages
        }

        hours = self.parse_hours(data.get("openingHours"))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, open_hours):
        opening_hours = OpeningHours()

        for weekday in open_hours:
            day = weekday.split(" ")[0]
            hours = weekday.split(" ")[1]
            open_time = hours.split("-")[0]
            close_time = hours.split("-")[1]
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
