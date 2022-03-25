# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class DunkinSpider(scrapy.Spider):
    name = "dunkindonuts"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    allowed_domains = ["dunkindonuts.com"]
    start_urls = [
        "https://locations.dunkindonuts.com/en",
    ]

    def parse(self, response):
        for href in response.xpath('//*[@class="Directory-content"]//@href').extract():
            yield scrapy.Request(response.urljoin(href))

        if response.css('[itemtype="https://schema.org/FastFoodRestaurant"]'):
            yield from self.parse_store(response)

    def parse_store(self, response):
        coords = json.loads(
            response.xpath('//script[@class="js-map-data"]/text()').get()
        )
        hours = json.loads(
            response.xpath('//script[@class="js-hours-config"]/text()').get()
        )
        opening_hours = OpeningHours()
        for row in hours["hours"]:
            day = row["day"][:2].capitalize()
            for i in row["intervals"]:
                start_hour, start_minute = divmod(i["start"], 100)
                end_hour, end_minute = divmod(i["end"], 100)
                start_time = f"{start_hour:02}:{start_minute:02}"
                end_time = f"{end_hour:02}:{end_minute:02}"
                opening_hours.add_range(day, start_time, end_time)

        address = response.css("[itemprop=address]")
        properties = {
            "ref": response.url.rsplit("/", 1)[1],
            "lat": coords["latitude"],
            "lon": coords["longitude"],
            "website": response.url,
            "addr_full": address.xpath(
                './/*[@itemprop="streetAddress"]/@content'
            ).get(),
            "city": address.xpath('.//*[@itemprop="addressLocality"]/@content').get(),
            "state": address.xpath('.//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": address.xpath('.//*[@itemprop="postalCode"]/text()').get(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').get(),
            "opening_hours": opening_hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
