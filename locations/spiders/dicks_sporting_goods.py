import re
import string

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class DicksSportingGoodsSpider(scrapy.Spider):
    name = "dicks_sporting_goods"
    item_attributes = {"brand": "Dick's Sporting Goods", "brand_wikidata": "Q5272601"}
    allowed_domains = ["dickssportinggoods.com"]
    start_urls = ("https://stores.dickssportinggoods.com/",)

    def parse_hours(self, response):
        days = response.xpath('//meta[@property="business:hours:day"]/@content').extract()
        start_times = response.xpath('//meta[@property="business:hours:start"]/@content').extract()
        end_times = response.xpath('//meta[@property="business:hours:end"]/@content').extract()

        opening_hours = OpeningHours()
        for day, open_time, close_time in zip(days, start_times, end_times):
            opening_hours.add_range(day=DAY_MAPPING[day], open_time=open_time, close_time=close_time)
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r"/(\d+)/$", response.url).group(1)
        name = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        shopping_center = string.capwords(
            "".join(response.xpath('//div[contains(@class, "shopping_center")]/text()').extract()).strip()
        )
        if shopping_center:
            name = ", ".join([name, shopping_center])

        yield Feature(
            lat=float(response.xpath('//meta[@property="place:location:latitude"]/@content').extract_first()),
            lon=float(response.xpath('//meta[@property="place:location:longitude"]/@content').extract_first()),
            street_address=response.xpath(
                '//meta[@property="business:contact_data:street_address"]/@content'
            ).extract_first(),
            city=response.xpath('//meta[@property="business:contact_data:locality"]/@content').extract_first(),
            state=response.xpath('//meta[@property="business:contact_data:region"]/@content').extract_first(),
            postcode=response.xpath('//meta[@property="business:contact_data:postal_code"]/@content').extract_first(),
            country=response.xpath('//meta[@property="business:contact_data:country_name"]/@content').extract_first(),
            phone=response.xpath('//meta[@property="business:contact_data:phone_number"]/@content').extract_first(),
            website=response.xpath('//meta[@property="business:contact_data:website"]/@content').extract_first(),
            ref=ref,
            name=name,
            opening_hours=self.parse_hours(response),
        )

    def parse_city(self, response):
        store_urls = response.xpath(
            '//ul[@class="city_contentlist"]/li//a[contains(text(), "Store Hours & Details")]/@href'
        ).extract()
        for url in store_urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_state(self, response):
        city_urls = response.xpath('//ul[@class="contentlist"]/li/a/@href').extract()
        for url in city_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_city,
            )

    def parse(self, response):
        state_urls = response.xpath('//ul[@class="contentlist"]/li/a/@href').extract()
        for url in state_urls:
            yield scrapy.Request(url=url, callback=self.parse_state)
