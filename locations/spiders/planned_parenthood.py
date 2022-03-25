# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class PlannedParenthoodSpider(scrapy.Spider):
    name = "planned_parenthood"
    item_attributes = {"brand": "Planned Parenthood"}
    allowed_domains = ["www.plannedparenthood.org"]
    start_urls = ("https://www.plannedparenthood.org/health-center",)

    def parse(self, response):
        state_urls = response.xpath(
            '//ul[@class="quicklist-list"]/li/a/@href'
        ).extract()
        for path in state_urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        venue_urls = response.xpath(
            '//ul[@class="quicklist-list"]/li/p/a/@href'
        ).extract()
        for path in venue_urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_venue,
                meta={"dont_redirect": True},
            )

    def parse_venue(self, response):
        if response is None:
            # Ignoring redirects
            return

        properties = {
            "addr_full": response.xpath(
                '//*[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//*[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//*[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//*[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//a[@itemprop="telephone"][@data-link]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
        }

        map_image_url = response.xpath(
            '//img[@class="address-map"]/@src'
        ).extract_first()
        match = re.search(r"center=(.*?),(.*?)&zoom", map_image_url)
        properties["lat"] = float(match.group(1))
        properties["lon"] = float(match.group(2))

        yield GeojsonPointItem(**properties)
