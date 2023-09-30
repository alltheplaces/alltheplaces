import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class ChuckECheeseSpider(scrapy.Spider):
    name = "chuckecheese"
    item_attributes = {"brand": "Chuck E Cheese", "brand_wikidata": "Q2438391"}
    allowed_domains = ["chuckecheese.com"]
    start_urls = ["https://locations.chuckecheese.com"]

    def parse(self, response):
        for href in response.xpath('//*[@class="Teaser-link" or @class="Directory-listLink"]/@href').extract():
            yield scrapy.Request(response.urljoin(href))

        if response.xpath('//*[@itemtype="http://schema.org/LocalBusiness"]'):
            yield from self.parse_store(response)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = list(dict.fromkeys(hours))

        for hour in hours:
            day, interval = hour.split(" ")
            if interval == "Closed":
                continue
            open_time, close_time = interval.split("-")

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            "ref": "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
            "street_address": response.xpath('//*[@class="c-address-street-1"]/text()').extract_first(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//*[@itemprop="addressCountry"]/text()').extract_first(),
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath('//*[@itemprop="longitude"]/@content').extract_first(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').extract_first(),
            "website": response.url,
        }

        hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)
