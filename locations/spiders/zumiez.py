# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ZumiezSpider(scrapy.Spider):
    download_delay = 0.1
    name = "zumiez"
    item_attributes = {"brand": "Zumiez", "brand_wikidata": "Q8075252"}
    allowed_domains = [
        "www.zumiez.com",
    ]
    start_urls = ("https://www.zumiez.com/storelocator/list/",)

    def parse(self, response):
        urls = response.xpath(
            '//div[@id="store-list-all"]/ul/li/ul/li/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()

        days = response.xpath(
            '//div[contains(@class, "storePage-hours")]/time/@datetime'
        ).extract()
        for day in days:
            day = day.replace("\xa0", " ")
            day = day.replace("-", " ")
            try:
                (d, ot, ct) = day.split()
            # Some stores may not operate on a specific day
            except ValueError:
                continue
            oh.add_range(d[:2], ot, ct, time_format="%I:%M%p")

        properties = {
            "addr_full": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@itemprop="telephone"]/a/text()'
            ).extract_first(),
            "city": response.xpath('//span[@itemprop="addressLocality"]/text()')
            .extract_first()
            .replace(",", ""),
            "state": response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "ref": response.xpath('//h3[@class="uppercase"]/text()').extract_first(),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
            "opening_hours": oh.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
