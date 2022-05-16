# -*- coding: utf-8 -*-
import re
import json
import scrapy
from locations.items import GeojsonPointItem


class FarmersInsuranceSpider(scrapy.Spider):
    download_delay = 0.2
    name = "farmers-insurance"
    item_attributes = {"brand": "Farmers Insurance", "brand_wikidata": "Q1396863"}
    allowed_domains = ["agents.farmers.com"]
    start_urls = ("https://agents.farmers.com/",)

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        state_urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()

        for url in state_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        city_urls = response.xpath('//a[@class="location-title-link"]/@href').extract()

        for url in city_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)
        properties = {
            "ref": ref.strip("/"),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "country": response.xpath(
                '//abbr[@class="c-address-country-name c-address-country-us"]/text()'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "website": response.url,
        }

        hours_data = self.parse_hours(
            response.xpath(
                '//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
            ).extract_first()
        )

        if hours_data:
            properties["opening_hours"] = hours_data
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours_data):
        if hours_data is None:
            return

        days = json.loads(hours_data)
        out_hours = []

        for day in days:
            start_day = day["day"][:2].title()
            intervals = day["intervals"]
            hours = [
                "%04d-%04d" % (interval["start"], interval["end"])
                for interval in intervals
            ]
            if len(intervals):
                out_hours.append("{} {}".format(start_day, ",".join(hours)))
        if len(out_hours):
            return "; ".join(out_hours)
