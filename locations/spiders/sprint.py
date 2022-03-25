# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SprintSpider(scrapy.Spider):
    name = "sprint"
    item_attributes = {"brand": "Sprint"}
    allowed_domains = ["sprint.com"]
    start_urls = ("https://www.sprint.com/locations/",)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for store_day in store_hours:
            day, open_close = store_day.split(" ")
            open_time, close_time = open_close.split("-")
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        state_urls = response.xpath('//a[@class="lm-homepage__state"]/@href').extract()
        for state_url in state_urls:
            yield scrapy.Request(response.urljoin(state_url), callback=self.parse_state)

    def parse_state(self, response):
        city_urls = response.xpath('//a[@class="lm-state__store"]/@href').extract()
        for city_url in city_urls:
            yield scrapy.Request(response.urljoin(city_url), callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": data["name"],
            "ref": data["branchCode"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(data.get("openingHoursSpecification", []))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
