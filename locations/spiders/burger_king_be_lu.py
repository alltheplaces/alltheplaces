import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BurgerKingBeLuSpider(scrapy.Spider):
    name = 'burger_king_be_lu'
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}
    download_delay = 2.0
    allowed_domains = ['www.burgerking.be']
    start_urls = [
        "https://stores.burgerking.be/nl/",
    ]

    def parse(self, response):
        for ldjson in response.xpath(
                '//script[@type="application/ld+json"]/text()'
        ).extract():
            graph = json.loads(ldjson)["@graph"]
            for data in graph:
                yield self.parse_restaurant(data)

    def parse_restaurant(self, data):
        if data["@type"] != "LocalBusiness":
            return

        opening_hours = OpeningHours()
        for spec in data["openingHoursSpecification"]:
            opening_hours.add_range(
                spec["dayOfWeek"][:2], spec["opens"], spec["closes"]
            )

        properties = {
            "ref": data["@id"],
            "website": data["url"],
            "name": data["name"],
            "phone": data["telephone"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "opening_hours": opening_hours.as_opening_hours(),
        }
        return GeojsonPointItem(**properties)
