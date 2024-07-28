import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class IhopSpider(scrapy.Spider):
    name = "ihop"
    item_attributes = {"brand": "IHOP", "brand_wikidata": "Q1185675"}
    allowed_domains = ["restaurants.ihop.com"]
    start_urls = ("https://restaurants.ihop.com/en-us",)

    def parse_opening_hours(self, hours):
        opening_hours = OpeningHours()

        for item in hours:
            day = item.xpath('.//span[@class="daypart"]/@data-daypart').extract_first()
            open_time = item.xpath('.//span[@class="time-open"]/text()').extract_first()
            close_time = item.xpath('.//span[@class="time-close"]/text()').extract_first()

            if not open_time:
                if item.xpath('.//span[@class="time"]/span/text()').extract_first() == "Open 24 Hours":
                    open_time = "12:00am"
                    close_time = "11:59pm"
                else:
                    continue

            opening_hours.add_range(
                day=day[:2],
                open_time=open_time.upper(),
                close_time=close_time.upper(),
                time_format="%I:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        state_urls = response.xpath('//div[@class="browse-container"]//li//a/@href').extract()
        for state_url in state_urls:
            yield scrapy.Request(url=state_url, callback=self.parse_state)

    def parse_state(self, response):
        city_urls = response.xpath('//ul[@class="map-list"]/li//a/@href').extract()
        for city_url in city_urls:
            yield scrapy.Request(url=city_url, callback=self.parse_city)

    def parse_city(self, response):
        location_urls = response.xpath('//div[@class="map-list-item-header"]/a/@href').extract()
        for location_url in location_urls:
            if location_url != "#":
                yield scrapy.Request(url=location_url, callback=self.parse_location)

    def parse_location(self, response):
        info_json = response.xpath(
            "//script[@type='application/ld+json' and contains(text(), 'geo')]/text()"
        ).extract_first()
        basic_info = json.loads(info_json)[0]

        point = {
            "lat": basic_info["geo"]["latitude"],
            "lon": basic_info["geo"]["longitude"],
            "name": basic_info["name"],
            "street_address": basic_info["address"]["streetAddress"],
            "city": basic_info["address"]["addressLocality"],
            "state": basic_info["address"]["addressRegion"],
            "postcode": basic_info["address"]["postalCode"],
            "phone": basic_info["address"]["telephone"],
            "website": basic_info["url"],
            "ref": "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
        }

        hours = self.parse_opening_hours(
            response.xpath('//div[contains(@class, "hide-mobile")]//div[@class="day-hour-row"]')
        )
        if hours:
            point["opening_hours"] = hours

        return Feature(**point)
