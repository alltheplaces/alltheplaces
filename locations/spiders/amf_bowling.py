import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class AmfBowlingSpider(scrapy.Spider):
    name = "amf_bowling"
    start_urls = ("https://www.amf.com/bowlero-location/finder?_format=json",)

    brands = {
        "AMF": {"brand": "AMF Bowling Center", "brand_wikidata": "Q4652616"},
        "Bowlero": {"brand": "Bowlero", "brand_wikidata": "Q17102967"},
        "Bowlmor": {"brand": "Bowlmor", "brand_wikidata": "Q4951260"},
    }

    def parse(self, response):
        for location in json.loads(response.body):
            item = Feature(
                name=location["name"],
                ref=location["id"],
                street_address=location["address1"],
                lat=location["lat"],
                lon=location["lng"],
                city=location["city"],
                state=location["state"],
                postcode=location["zip"],
                country="US",
                phone=location["phone"],
                website=location["url"],
            )

            if brand := self.brands.get(location["brand"]):
                item.update(brand)

            apply_category(Categories.BOWLING, item)

            yield item
