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

        return opening_hours

    def parse_store(self, response):
        long = response.xpath('//script[contains(text(), "lng")]/text()').re_first(r'lng":"([\d\.\-]+)"')
        lat = response.xpath('//script[contains(text(), "lng")]/text()').re_first(r'lat":"([\d\.\-]+)"')

        properties = {
            "ref": response.url,
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').get(),
            "street_address": response.xpath('normalize-space(//span[@itemprop="StreetAddress"]//text())').get(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').get(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').get(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').get(),
            "country": "US",
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]//text())').get(),
            "website": response.url,
            "lat": lat,
            "lon": long,
        }

        properties["opening_hours"] = self.parse_hours(
            response.xpath('//*[@itemprop="openingHours"]/@content').getall()
        )
        yield Feature(**properties)

    def parse(self, response):
        for url in response.xpath('//span[@class="store-info"]/a/@href').getall():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
