# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PublicStorageSpider(scrapy.Spider):
    name = "public_storage"
    item_attributes = {"brand": "Public Storage"}
    allowed_domains = ["www.publicstorage.com"]
    start_urls = ("https://www.publicstorage.com/sitemap_plp.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.load_store,
            )

    def load_store(self, response):
        ldjson = response.xpath('//link[@type="application/ld+json"]/@href').get()
        yield scrapy.Request(response.urljoin(ldjson), callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            for day in hour["dayOfWeek"]:
                opening_hours.add_range(
                    day=day[:2],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        data = response.json()["@graph"][0]

        properties = {
            "ref": data["@id"],
            "website": data["url"],
            "opening_hours": self.parse_hours(data["openingHoursSpecification"]),
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["telephone"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
        }

        yield GeojsonPointItem(**properties)
