# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BenihanaSpider(scrapy.Spider):
    download_delay = 0.2
    name = "benihana"
    item_attributes = {"brand": "Benihana"}
    allowed_domains = ["benihana.com"]

    def start_requests(self):
        yield scrapy.Request(
            "https://www.benihana.com/wp-content/themes/grandrestaurant-child/js/locations.json",
            callback=self.set_locations,
        )
        yield scrapy.Request("https://www.benihana.com/locations/")

    def set_locations(self, response):
        self.locations = response.json()

    def parse(self, response):
        urls = response.xpath('//div[@class="location-link"]/a/@href').extract()

        for url in urls:
            if (
                url != "http://www.dignityhealthsportspark.com/"
                or url != "https://www.sprintcenter.com/"
            ):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)

    def parse_stores(self, response):
        delivery_only = response.xpath(
            '//div[@class="hours-wrapper"]/p/strong/text()'
        ).extract_first()
        if delivery_only != "DELIVERY HOURS":
            locationid = re.search(r".*/locations/(.*)/$", response.url).groups()[0]
            location = [
                loc for loc in self.locations if loc["LocationId"] == locationid
            ][0]
            properties = {
                "addr_full": response.xpath('//span[@itemprop="streetAddress"]/text()')
                .extract_first()
                .strip(","),
                "phone": response.xpath(
                    '//span[@itemprop="telephone"]/text()'
                ).extract_first(),
                "name": response.xpath(
                    '//h2[@class="ppb_title"]/text()'
                ).extract_first(),
                "city": response.xpath('//span[@itemprop="addressLocality"]/text()')
                .extract_first()
                .strip(","),
                "state": response.xpath(
                    '//span[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//span[@itemprop="postalCode"]/text()'
                ).extract_first(),
                "ref": locationid,
                "website": response.url,
                "lat": float(location["lat"]),
                "lon": float(location["lng"]),
            }

            yield GeojsonPointItem(**properties)
