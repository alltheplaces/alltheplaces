import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class MicroCenterSpider(scrapy.Spider):
    name = "micro_center"
    item_attributes = {"brand": "Micro Center", "brand_wikidata": "Q6839153"}
    allowed_domains = ["www.microcenter.com"]
    start_urls = ("https://www.microcenter.com/site/stores/default.aspx",)

    def parse(self, response):
        for url in response.xpath('//div[@class="location-container"]//a/@href').extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        for ldjson in response.xpath('//script[@type="application/ld+json"]/text()').extract():
            data = json.loads(ldjson)
            if data["@type"] == "ComputerStore":
                break
        else:
            raise ValueError

        opening_hours = OpeningHours()
        for spec in data["openingHoursSpecification"]:
            day = spec["dayOfWeek"][:2]
            open_time = spec["opens"] + ":00"
            close_time = spec["closes"] + ":00"
            opening_hours.add_range(day, open_time, close_time)

        properties = {
            "ref": response.url,
            "name": data["name"],
            "website": response.url,
            "phone": data["telephone"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "opening_hours": opening_hours.as_opening_hours(),
        }

        yield Feature(**properties)
