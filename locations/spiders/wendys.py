from locations.hours import OpeningHours
import scrapy
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class WendysSpider(scrapy.Spider):
    name = "wendys"
    item_attributes = {"brand": "Wendy's", "brand_wikidata": "Q550258"}
    allowed_domains = ["locations.wendys.com"]
    start_urls = ("https://locations.wendys.com/index.html",)

    def parse_hours(self, hours_elements):
        o = OpeningHours()
        for s in hours_elements:
            day, times = s.split(" ", 1)

            if times == "Closed":
                continue

            if times == "All Day":
                open_time = "00:00"
                close_time = "23:59"
            else:
                open_time, close_time = times.split("-", 1)

            o.add_range(day, open_time=open_time, close_time=close_time)

        return o.as_opening_hours()

    def parse(self, response):
        for url in response.xpath('//a[@class="Directory-listLink"]/@href').extract():
            yield scrapy.Request(response.urljoin(url))

        for url in response.xpath(
            '//a[@class="Teaser-titleLink Link--big"]/@href'
        ).extract():
            yield scrapy.Request(response.urljoin(url))

        if response.xpath('//span/meta[@itemprop="longitude"]/@content'):
            properties = {
                "ref": response.url,
                "addr_full": response.xpath(
                    '//meta[@itemprop="streetAddress"]/@content'
                ).extract_first(),
                "city": response.xpath(
                    '//meta[@itemprop="addressLocality"]/@content'
                ).extract_first(),
                "state": response.xpath(
                    '//abbr[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                "postcode": response.xpath('//span[@itemprop="postalCode"]/text()')
                .extract_first()
                .strip(),
                "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()')
                .extract_first()
                .strip(),
                "phone": response.xpath(
                    '//span[@itemprop="telephone"]/text()'
                ).extract_first(),
                "opening_hours": self.parse_hours(
                    response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
                ),
                "lon": response.xpath(
                    '//span/meta[@itemprop="longitude"]/@content'
                ).extract_first(),
                "lat": response.xpath(
                    '//span/meta[@itemprop="latitude"]/@content'
                ).extract_first(),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
