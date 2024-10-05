import html
import json

import scrapy

from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature


class ChilisSpider(scrapy.Spider):
    name = "c"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    allowed_domains = ["chilis.com"]
    download_delay = 0.5
    start_urls = ("https://www.chilis.com/locations/us/all",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            opening_hours.add_range(
                day=DAYS_EN[hour["dayOfWeek"]],
                open_time=hour["opens"],
                close_time=hour["closes"],
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').extract()
        data = [json.loads(x) for x in scripts if json.loads(x)["@type"] == "Restaurant"][0]

        properties = {
            "street_address": html.unescape(data["address"]["streetAddress"]),
            "phone": data["telephone"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": "US",
            "ref": data["branchCode"],
            "website": response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "name": html.unescape(data["name"]),
        }
        hours = self.parse_hours(data["openingHoursSpecification"])

        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse_city(self, response):
        urls = response.xpath('//a[text()="Details"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse(self, response):
        urls = response.xpath('//div[contains(@class, "city-locations")]//a[@class="city-link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)
