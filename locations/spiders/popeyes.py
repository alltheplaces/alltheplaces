# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class PopeyesSpider(scrapy.Spider):

    name = "popeyes"
    item_attributes = {
        "brand": "Popeyes Louisiana Kitchen",
        "brand_wikidata": "Q1330910",
    }
    allowed_domains = ["www.popeyes.com", "locations.popeyes.com"]
    download_delay = 0.2
    start_urls = ("https://locations.popeyes.com/",)

    def parse_location(self, location):
        hours = json.loads(
            location.xpath(
                '//script[@type="text/data"][@class="js-hours-config"]/text()'
            ).extract_first()
        )
        opening_hours = OpeningHours()
        for row in hours["hours"]:
            day = row["day"][:2].capitalize()
            for interval in row["intervals"]:
                start_hour, start_minute = divmod(interval["start"], 100)
                end_hour, end_minute = divmod(interval["end"], 100)
                start_time = f"{start_hour:02}:{start_minute:02}"
                end_time = f"{end_hour:02}:{end_minute:02}"
                opening_hours.add_range(day, start_time, end_time)

        props = {
            "addr_full": location.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "lon": float(
                location.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "lat": float(
                location.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "city": location.css("span.Address-city::text").extract_first(),
            "postcode": location.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "state": location.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "phone": location.xpath(
                '//div[@itemprop="telephone"]/text()'
            ).extract_first(),
            "ref": location.url,
            "website": location.url,
            "opening_hours": opening_hours.as_opening_hours(),
        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, city):
        locations = city.xpath('//a[@data-ya-track="visitpage"]/@href').extract()
        for location in locations:
            yield scrapy.Request(
                url=city.urljoin(location), callback=self.parse_location
            )

    def parse_state(self, state):
        cities = state.xpath('//a[@data-ya-track="todirectory"]/@href').extract()
        for city in cities:
            url = state.urljoin(city)
            if url.count("/") < 5:
                callback = self.parse_city_stores
            else:
                callback = self.parse_location
            yield scrapy.Request(url=url, callback=callback)

    def parse(self, response):
        states = response.xpath('//a[@data-ya-track="todirectory"]/@href').extract()
        for state in states:
            yield scrapy.Request(url=response.urljoin(state), callback=self.parse_state)
