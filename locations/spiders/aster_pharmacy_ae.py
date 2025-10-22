from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AsterPharmacyAESpider(Spider):
    name = "aster_pharmacy_ae"
    item_attributes = {"brand": "Aster Pharmacy", "brand_wikidata": "Q124453575"}
    no_refs = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://www.asterpharmacy.ae/aster-api/REST/getStore", data={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = Feature()
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["addr_full"] = location["locationname"]
            item["city"] = location["city"]
            item["phone"] = location["mobilenumber"]

            apply_category(Categories.PHARMACY, item)

            yield item
