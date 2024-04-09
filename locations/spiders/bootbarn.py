import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class BootbarnSpider(scrapy.Spider):
    name = "bootbarn"
    item_attributes = {"brand": "Boot Barn", "brand_wikidata": "Q109825187"}
    allowed_domains = ["bootbarn.com"]
    start_urls = [
        "https://www.bootbarn.com/stores-all",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for i in range(0, len(hours), 2):
            day = hours[i]
            if "CLOSED" in hours[i + 1]:
                continue
            else:
                open_time, close_time = hours[i + 1].split(" - ")
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I%p" if ":" not in open_time else "%I:%M%p",
                )

        return opening_hours

    def parse_location(self, response):
        properties = {
            "ref": re.search(r".+/?StoreID=(.+)", response.url).group(1),
            "name": response.xpath('normalize-space(//span[@class="store-name"]//text())').extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@class="store-address1"]//text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@class="store-address-city"]//text())').extract_first(),
            "state": response.xpath('normalize-space(//span[@class="store-address-state"]//text())').extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@class="store-address-postal-code"]//text())'
            ).extract_first(),
            "phone": response.xpath('normalize-space(//span[@class="store-phone"]//text())').extract_first(),
            "website": response.url,
            "lat": response.xpath('//div[@id="store-detail-coords"]/@data-lat').extract_first(),
            "lon": response.xpath('//div[@id="store-detail-coords"]/@data-lon').extract_first(),
        }

        properties["opening_hours"] = self.parse_hours(
            response.xpath(
                '//div[@class="store-details-section"]//div[@class="store-hours-days"]/span/text()'
            ).extract()
        )

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//div[@class="store"]/div[@class="city"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)
