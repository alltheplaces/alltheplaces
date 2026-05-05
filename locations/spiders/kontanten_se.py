from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KontantenSESpider(Spider):
    name = "kontanten_se"
    item_attributes = {"brand": "Kontanten", "brand_wikidata": "Q126902178"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://kontanten.se/wp-admin/admin-ajax.php",
            formdata={
                "action": "markers_data",
                "call": "markers",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            coordinates = (store.get("geometry") or {}).get("coordinates") or [None, None]
            item = Feature()
            item["ref"] = store.get("id")
            item["located_in"] = (store.get("place") or "").removeprefix("Kontanten ").strip()
            item["street_address"] = store.get("address")
            item["postcode"] = store.get("postal")
            item["city"] = store.get("city")
            item["lat"] = coordinates[0]
            item["lon"] = coordinates[1]
            apply_category(Categories.ATM, item)
            yield item
