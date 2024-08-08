import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class JuicelandSpider(scrapy.Spider):
    name = "juiceland"
    item_attributes = {"brand": "JuiceLand", "brand_wikidata": "Q123022671"}
    allowed_domains = ["juiceland.com"]
    start_urls = [
        "https://www.juiceland.com/all-locations/",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                day, open_time, close_time = re.search(r"([A-Za-z]{2})\s([\d:]+)-([\d:]+)", hour).groups()
            except:
                continue
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        long = response.xpath('//script[contains(text(), "lng")]/text()').re_first(r'lng":"([\d\.\-]+)"')
        lat = response.xpath('//script[contains(text(), "lng")]/text()').re_first(r'lat":"([\d\.\-]+)"')

        properties = {
            "ref": response.url,
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@itemprop="StreetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').extract_first(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            "country": "US",
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": lat,
            "lon": long,
        }

        hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())

        if hours:
            properties["opening_hours"] = hours
        yield Feature(**properties)

    def parse(self, response):
        for url in response.xpath('//span[@class="store-info"]/a/@href').extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
