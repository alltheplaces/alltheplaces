# -*- coding: utf-8 -*-
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MichaelsSpider(scrapy.Spider):
    download_delay = 0.2
    name = "michaels"
    item_attributes = {"brand": "Michaels", "brand_wikidata": "Q6835667"}
    allowed_domains = ["michaels.com"]
    start_urls = ("http://locations.michaels.com/",)

    def parse(self, response):
        urls = response.xpath('//a[@class="contentlist_item"]/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        location_urls = response.xpath('//a[@class="contentlist_item"]/@href').extract()

        for url in location_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        city_urls = response.xpath('//div[@id="locations"]//ul/a/@href').extract()

        for url in city_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "ref": ref.strip("/"),
            "addr_full": response.xpath(
                '//meta[@property="business:contact_data:street_address"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@property="business:contact_data:locality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//meta[@property="business:contact_data:region"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//meta[@property="business:contact_data:postal_code"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                '//meta[@property="business:contact_data:phone_number"]/@content'
            ).extract_first(),
            "name": response.xpath('//div[@class="address"]/span/text()').extract()[1],
            "country": response.xpath(
                '//meta[@property="business:contact_data:country_name"]/@content'
            ).extract_first(),
            "lat": float(
                response.xpath(
                    '//meta[@property="place:location:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="place:location:longitude"]/@content'
                ).extract_first()
            ),
            "website": response.url,
        }

        hours = self.parse_hours(
            response.xpath('//time[@itemprop="openingHours"]/@datetime').extract()
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()
        weekdays = response

        for weekday in weekdays:
            day, hrs = weekday.split(" ")
            open, close = hrs.split("-")
            opening_hours.add_range(
                day, open_time=open, close_time=close, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()
