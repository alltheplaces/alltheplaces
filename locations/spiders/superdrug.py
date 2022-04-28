# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SuperdrugSpider(scrapy.Spider):
    name = "superdrug"
    item_attributes = {"brand": "Superdrug", "brand_wikidata": "Q7643261"}
    allowed_domains = ["superdrug.com"]
    download_delay = 0.5

    start_urls = ["https://www.superdrug.com/stores/a-to-z"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def parse(self, response):
        urls = response.xpath('//a[@class="row store-link"]/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": data["name"].replace("Superdrug", "").strip(),
            "ref": data["@id"],
            "street_address": data["address"]["streetAddress"]
            .replace("Superdrug", "")
            .strip(),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "website": response.url,
            "lat": float(
                response.xpath(
                    '//div[@class="store-locator store-locator__overview"]/@data-lat'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//div[@class="store-locator store-locator__overview"]/@data-lng'
                ).extract_first()
            ),
        }

        oh = OpeningHours()

        for rule in data["OpeningHoursSpecification"]:
            oh.add_range(
                day=rule["dayOfWeek"][0:2],
                open_time=rule["opens"],
                close_time=rule["closes"],
                time_format="%I:%M %p",
            )

        yield GeojsonPointItem(**properties)
