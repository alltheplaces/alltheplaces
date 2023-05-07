import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class DennysSpider(scrapy.Spider):
    name = "dennys"
    item_attributes = {"brand": "Denny's", "brand_wikidata": "Q1189695"}
    allowed_domains = ["locations.dennys.com"]
    start_urls = ("https://locations.dennys.com/",)

    def parse_hours(self, hours_container):
        opening_hours = OpeningHours()

        for row in hours_container.xpath('.//*[@itemprop="openingHours"]/@content').extract():
            day, interval = row.split(" ", 1)
            if interval == "Closed":
                continue
            if interval == "All Day":
                interval = "00:00-00:00"
            open_time, close_time = interval.split("-")
            opening_hours.add_range(day, open_time, close_time)
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "ref": response.url.split("/")[-1],
            "website": response.url,
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
        }
        phone = response.xpath('//div[@itemprop="telephone"]/text()').extract_first()
        if phone:
            properties["phone"] = phone

        if hours_container := response.xpath('//table[@class="c-hours-details"]'):
            properties["opening_hours"] = self.parse_hours(hours_container[0])

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        is_store_list = response.xpath('//section[contains(@class,"LocationList")]').extract()

        if not urls and is_store_list:
            urls = response.xpath('//a[contains(@class,"Teaser-titleLink")]/@href').extract()

        for url in urls:
            if re.search(r".{2}/.+/.+", url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
