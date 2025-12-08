from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RoyalBankOfCanadaCASpider(JSONBlobSpider):
    name = "royal_bank_of_canada_ca"
    item_attributes = {"brand_wikidata": "Q735261"}
    locations_key = "locations"

    def start_requests(self):
        for city in city_locations("CA", min_population=20000):
            yield scrapy.Request(
                url=f'https://maps.rbcroyalbank.com/api/?q={city["name"]}',
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if item.get("addr_full"):
            item["street_address"] = item.pop("addr_full")
        item["lat"], item["lon"] = feature.pop("location")
        if feature["branch"] and feature["atm"]:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        elif feature["branch"] and not feature["atm"]:
            apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.ATM, item)
        yield item
