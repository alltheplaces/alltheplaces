import re

import scrapy

from locations.items import GeojsonPointItem


class TacoJohns(scrapy.Spider):
    name = "taco_johns"
    allowed_domains = ["tacojohns.com"]
    download_delay = 0.2
    start_urls = ("https://locations.tacojohns.com/",)

    state_pattern = re.compile(r"^[a-z]{2}(\.html)$")
    city_pattern = re.compile(r"^[a-z]{2}\/.+(\.html)$")
    location_pattern = re.compile(r"^[a-z]{2}\/.+\/.+(\.html)$")

    def parse(self, response):
        urls = response.xpath(
            '//li[@class="c-directory-list-content-item"]//@href'
        ).extract()
        for url in urls:
            if self.state_pattern.match(url.strip()):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_state)
            elif self.location_pattern.match(url.strip()):
                yield scrapy.Request(
                    response.urljoin(url), callback=self.parse_location
                )
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_state(self, response):
        urls = response.xpath(
            '//li[@class="c-directory-list-content-item"]//@href'
        ).extract()
        for url in urls:
            if self.location_pattern.match(url.strip()):
                yield scrapy.Request(
                    response.urljoin(url), callback=self.parse_location
                )
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        urls = response.xpath(
            '//*[@class="c-location-grid-item-link page-link hidden-xs"]//@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):

        properties = {
            "ref": response.url,
            "name": response.xpath('//div[@itemprop="name"]//text()').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//*[@itemprop="streetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]//text()'
            ).extract_first(),
            "state": response.xpath(
                '//*[@itemprop="addressRegion"]//text()'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "country": "USA",
            "phone": response.xpath('//span[@id="telephone"]//text()').extract_first(),
            "website": response.url,
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath(
                '//*[@itemprop="longitude"]/@content'
            ).extract_first(),
        }

        yield GeojsonPointItem(**properties)
