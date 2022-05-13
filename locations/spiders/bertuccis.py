# -*- coding: utf-8 -*-
import json
import re

import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BertuccisSpider(scrapy.Spider):
    name = "bertuccis"
    item_attributes = {"brand": "Bertucci's", "brand_wikidata": "Q4895917"}
    allowed_domains = ["locations.bertuccis.com"]
    start_urls = ["https://locations.bertuccis.com/sitemap.xml"]

    def parse(self, response):
        for url in response.xpath('//*[local-name()="loc"]/text()').extract():
            if (
                url.startswith("https://locations.bertuccis.com/us/")
                and url.count("/") >= 6
            ):
                yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        store = response.xpath('//section[@class="Nap l-container"]')
        name = "".join(store.xpath('.//*[@itemprop="name"]//text()').extract())
        street = "".join(
            store.xpath('.//*[@itemprop="streetAddress"]//text()').extract()
        ).strip()
        city = (
            store.xpath('.//*[@itemprop="addressLocality"]/text()')
            .extract_first()
            .strip()
        )
        state = (
            store.xpath('.//*[@itemprop="addressRegion"]/text()')
            .extract_first()
            .strip()
        )
        postcode = (
            store.xpath('.//*[@itemprop="postalCode"]/text()').extract_first().strip()
        )
        phone = store.xpath('.//*[@itemprop="telephone"]/text()').extract_first()
        lat = store.xpath('.//*[@itemprop="latitude"]/@content').extract_first()
        lon = store.xpath('.//*[@itemprop="longitude"]/@content').extract_first()
        hours = store.xpath(
            './/*[contains(@class, "js-location-hours")]/@data-days'
        ).extract_first()
        try:
            opening_hours = self.parse_hours(json.loads(hours))
        except ValueError:
            opening_hours = None
        properties = {
            "name": name,
            "ref": re.findall(
                r"\"ids\":([0-9]+),\"pageSetId\":\"Locations\"", response.text
            )[0],
            "street": street,
            "city": city,
            "postcode": postcode,
            "state": state,
            "country": "USA",
            "lat": float(lat),
            "lon": float(lon),
            "phone": phone,
            "website": response.url,
            "opening_hours": opening_hours,
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.get("day").title()
            for interval in weekday.get("intervals", []):
                open_time = str(interval.get("start"))
                close_time = str(interval.get("end"))
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()
