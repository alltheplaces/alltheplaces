from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RoyalBankOfCanadaCASpider(JSONBlobSpider):
    name = "royal_bank_of_canada_ca"
    item_attributes = {"brand": "RBC", "brand_wikidata": "Q735261"}
    locations_key = "locations"

    async def start(self):
        for city in city_locations("CA", min_population=20000):
            yield scrapy.Request(
                url=f'https://maps.rbcroyalbank.com/api/?q={city["name"]}',
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["lat"], item["lon"] = feature.get("location")

        if feature["branch"]:
            item.pop("name")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, feature["atm"])
        else:
            item["located_in"] = item.pop("name")
            apply_category(Categories.ATM, item)

        yield item
