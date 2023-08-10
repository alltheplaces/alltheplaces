import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class RedRobinSpider(scrapy.Spider):
    name = "red_robin"
    item_attributes = {"brand": "Red Robin", "brand_wikidata": "Q7304886"}
    allowed_domains = ["locations.redrobin.com"]
    start_urls = ("https://locations.redrobin.com/",)

    def parse(self, response):
        for href in response.css("ul.sb-directory-list ::attr(href)").extract():
            yield scrapy.Request(response.urljoin(href))

        for ldjson in response.xpath('//script[@type="application/ld+json"]/text()').extract():
            data = json.loads(ldjson)
            if data["@type"] == "Restaurant":
                yield self.parse_store(response, data)

    def parse_store(self, response, data):
        hours = OpeningHours()
        for row in data["openingHoursSpecification"]:
            if not {"opens", "closes"} <= row.keys():
                continue
            day = row["dayOfWeek"].strip("https://schema.org/")[:2]
            hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")
        properties = {
            "name": data["name"],
            "ref": response.url.split("/")[-2],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"]["name"],
            "phone": data["telephone"],
            "opening_hours": hours.as_opening_hours(),
            "website": response.url,
        }
        return Feature(**properties)
