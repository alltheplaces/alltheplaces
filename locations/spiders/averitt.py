# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AverittSpider(scrapy.Spider):
    name = "averitt"
    item_attributes = {"brand": "Averitt Express", "brand_wikidata": "Q4828320"}
    allowed_domains = ["averittexpress.com"]
    start_urls = [
        "https://www.averittexpress.com/resources/facility-locator",
    ]

    def parse(self, response):
        states = response.xpath('//select[@name="state"]/option/@value').extract()
        for state in states:
            if state == "0":
                continue
            yield scrapy.FormRequest(
                url=response.urljoin("/resources/facility-locator/results"),
                method="POST",
                formdata={"state": state},
                meta={"state": state},
                callback=self.parse_state,
            )

    def parse_state(self, response):
        centers = response.xpath(
            '//section[contains(@class, "content-main")]//div[@class="grid"]//a/@href'
        ).extract()
        for center in centers:
            yield scrapy.Request(response.urljoin(center), callback=self.parse_center)

    def parse_center(self, response):
        map_url = response.xpath(
            '//div[@id="google-map"]/@data-iframe-src'
        ).extract_first()
        try:
            lat, lon = re.search(r"ll=([\d\-\.]+),([\d\-\.]+)&?", map_url).groups()
        except:
            lat, lon = None, None

        properties = {
            "ref": "_".join(
                re.search(r".+/(.+?)/(.+?)/?(?:\.jsp|$)", response.url).groups()
            ),
            "name": response.xpath(
                '//section[contains(@class, "content-main")]//h4/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@class="street-address"]//text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@class="locality"]//text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@class="region"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@class="postal-code"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
        }

        yield GeojsonPointItem(**properties)
