# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "SUNDAY": "Su",
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
}


class BloomingdalesSpider(scrapy.Spider):
    name = "bloomingdales"
    item_attributes = {"brand": "Bloomingdale's", "brand_wikidata": "Q283383"}
    allowed_domains = ["bloomingdales.com"]
    download_delay = 0.2
    start_urls = ("https://locations.bloomingdales.com/",)

    def parse_hours(self, hours):
        hours = json.loads(hours)
        opening_hours = OpeningHours()

        for hour in hours:
            if hour["intervals"]:
                opening_hours.add_range(
                    day=DAY_MAPPING[hour["day"]],
                    open_time=str(hour["intervals"][0]["start"]),
                    close_time=str(hour["intervals"][0]["end"]),
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath(
            '//li[@class="c-LocationGridList-item"]//a[contains(text(), "Website")]/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):

        brand = response.xpath(
            '//span[@class="LocationName-brand"]/text()'
        ).extract_first()
        name = response.xpath(
            '//span[@class="LocationName-geo"]/text()'
        ).extract_first()

        properties = {
            "name": brand + " " + name,
            "addr_full": response.xpath(
                '//span[contains(@class, "c-address-street-1")]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()')
            .extract_first()
            .strip(),
            "country": response.xpath(
                '//abbr[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "ref": re.search(r".*/(.*)$", response.url).groups()[0],
            "lat": response.xpath(
                '//span[@class="coordinates"]/meta[@itemprop="latitude"]/@content'
            ).extract_first(),
            "lon": response.xpath(
                '//span[@class="coordinates"]/meta[@itemprop="longitude"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "website": response.url,
        }

        hours = self.parse_hours(
            response.xpath(
                '//span[contains(@class, "c-location-hours-today")]/@data-days'
            ).extract_first()
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
