import scrapy
import re
from locations.items import GeojsonPointItem


class SunglassHutSpider(scrapy.Spider):
    name = "sunglass_hut"
    item_attributes = {"brand": "Sunglass Hut"}
    allowed_domains = ["stores.sunglasshut.com"]
    start_urls = ("https://stores.sunglasshut.com/",)

    def parse_opening_hours(self, opening_hours):
        return ";".join(opening_hours)

    def parse(self, response):
        urls = response.xpath(
            '//a[@class="c-directory-list-content-item-link" or @class="c-location-grid-item-link"]/@href'
        ).extract()
        # If cannot find 'c-directory-list-content-item-link' or 'c-location-grid-item-link' then this is a store page
        if len(urls) == 0:
            properties = {
                "addr_full": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//span[@itemprop="streetAddress"]/text())'
                ).extract_first(),
                "city": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//span[@itemprop="addressLocality"]/text())'
                )
                .extract_first()
                .strip(","),
                "state": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//span[@itemprop="addressRegion"]/text())'
                ).extract_first(),
                "postcode": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//span[@itemprop="postalCode"]/text())'
                ).extract_first(),
                "phone": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//span[@itemprop="telephone"]/text())'
                ).extract_first(),
                "ref": response.url,
                "website": response.url,
                "lat": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//meta[@itemprop="latitude"]/@content)'
                ).extract_first(),
                "lon": response.xpath(
                    'normalize-space(//div[@class="c-location-info"]//meta[@itemprop="longitude"]/@content)'
                ).extract_first(),
                "opening_hours": self.parse_opening_hours(
                    response.xpath('//meta[@itemprop="openingHours"]/@content').getall()
                ),
            }
            yield GeojsonPointItem(**properties)
        else:
            for path in urls:
                yield scrapy.Request(response.urljoin(path), callback=self.parse)
