# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class PetcoSpider(scrapy.Spider):
    name = "petco"
    item_attributes = {"brand": "Petco"}
    allowed_domains = ["stores.petco.com"]
    start_urls = ("https://stores.petco.com/",)

    def store_hours(self, store_hours):
        store_hours = store_hours.strip()

        day_groups = []
        for day_range in store_hours.splitlines():
            (days, hours) = day_range.split(" ", 1)

            # They explicitly say 'closed' for days that are closed
            if hours == "Closed":
                continue

            # Single days have a colon on the right side
            days = days.rstrip(":")

            # Strip out the spaces in the time range
            hours = hours.replace(" ", "")

            day_groups.append("{} {}".format(days, hours))

        return "; ".join(day_groups)

    def parse(self, response):
        for path in response.xpath('//a[@data-gaq="List, Region"]/@href'):
            yield scrapy.Request(
                response.urljoin(path.extract()),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for path in response.xpath('//a[@data-gaq="List, City"]/@href'):
            yield scrapy.Request(
                response.urljoin(path.extract()),
                callback=self.parse_city,
            )

    def parse_city(self, response):
        for path in response.xpath(
            '//a[@class="gaq-link"][@data-gaq="List, Location"]/@href'
        ):
            yield scrapy.Request(
                response.urljoin(path.extract()),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        # There are newlines in the opening hours, which is bad JSON. We turn
        # off strict mode so Python's JSON library will parse it.
        json_content = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        data = json.loads(json_content, strict=False)
        store_data = data[0]

        properties = {
            "website": store_data["url"],
            "name": store_data["name"],
            "phone": store_data["address"]["telephone"],
            "ref": store_data["url"],
            "addr_full": store_data["address"]["streetAddress"],
            "postcode": store_data["address"]["postalCode"],
            "state": store_data["address"]["addressRegion"],
            "city": store_data["address"]["addressLocality"],
            "lon": float(store_data["geo"]["longitude"]),
            "lat": float(store_data["geo"]["latitude"]),
        }

        opening_hours = self.store_hours(store_data["openingHours"])
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
