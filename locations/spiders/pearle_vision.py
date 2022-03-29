# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PearleVisionSpider(scrapy.Spider):
    name = "pearle_vision"
    item_attributes = {"brand": "Pearle Vision"}
    allowed_domains = ["pearlevision.com"]
    download_delay = 1

    def start_requests(self):
        base_url = "https://www.pearlevision.com/webapp/wcs/stores/servlet/AjaxStoreLocatorResultsView?storeId=12002&catalogId=15951&langId=-1&resultSize=100&latitude={lat}&longitude={lng}&location=dallas%2C+tx"

        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        urls = response.xpath('//*[@class="location-details-link"]/@href').extract()

        for path in urls:
            yield scrapy.Request(url=response.urljoin(path), callback=self.parse)

    def parse(self, response):
        coords = response.xpath('//script[@type="text/javascript"]').extract()

        for data in coords:
            if "LatLng" in data:
                lat = re.search(r'LatLng\(parseFloat\("(\d*.\d*)"', data).groups()[0]
                lng = re.search(r',parseFloat\("(-\d*.\d*)"', data).groups()[0]

        properties = {
            "ref": "_".join(
                re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()
            ),
            "name": response.xpath('//*[@class="storeInfo"]/h2/text()').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//*[@class="storeInfo"]/p/text())'
            ).extract_first(),
            "city": re.search(
                r"^(.*),",
                response.xpath(
                    'normalize-space(//*[@class="storeInfo"]/p/text()[2])'
                ).extract_first(),
            ).groups()[0],
            "state": re.search(
                r",\s([A-Z]{2})\s",
                response.xpath(
                    'normalize-space(//*[@class="storeInfo"]/p/text()[2])'
                ).extract_first(),
            ).groups()[0],
            "postcode": re.search(
                r"[A-Z]{2}\s(.*)$",
                response.xpath(
                    'normalize-space(//*[@class="storeInfo"]/p/text()[2])'
                ).extract_first(),
            ).groups()[0],
            "country": "US",
            "lat": lat,
            "lon": lng,
            "phone": response.xpath('//*[@class="tel"]/text()').extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
