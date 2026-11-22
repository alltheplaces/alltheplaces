import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class MgMotorGBSpider(Spider):
    name = "mg_motor_gb"
    item_attributes = {"brand": "MG", "brand_wikidata": "Q1881443"}
    start_urls = ["https://www.mg.co.uk/map"]

    def parse(self, response: Response) -> Iterable[Feature]:
        dealers = json.loads(
            response.xpath('//script[@type="application/ld+json"][contains(., "ItemList")]/text()').get()
        )
        for entry in dealers["itemListElement"]:
            dealer = entry["item"]
            item = Feature()
            item["ref"] = "{}_{}".format(dealer["name"], dealer["address"]["postalCode"])
            item["name"] = dealer["name"]
            item["street_address"] = dealer["address"]["streetAddress"]
            item["postcode"] = dealer["address"]["postalCode"]
            item["city"] = dealer["address"]["addressLocality"]
            item["country"] = "GB"
            item["lat"] = dealer["geo"]["latitude"]
            item["lon"] = dealer["geo"]["longitude"]
            item["phone"] = dealer["telephone"]
            item["website"] = dealer.get("url")
            # The page no longer flags sales and service separately, so every dealer is a sales dealer.
            apply_category(Categories.SHOP_CAR, item)
            yield item
