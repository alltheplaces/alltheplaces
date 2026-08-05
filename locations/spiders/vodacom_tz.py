from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VodacomTZSpider(JSONBlobSpider):
    name = "vodacom_tz"
    item_attributes = {"brand": "Vodacom Tanzania", "brand_wikidata": "Q7939274"}
    locations_key = "data"
    api = "https://myvodacom.vodacom.co.tz/app/digital-service-engine/api/v1/web/vodacom-shop-form"

    async def start(self) -> Any:
        yield Request(url=f"{self.api}/region", callback=self.parse_regions)

    def parse_regions(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["data"]:
            yield Request(url=f"{self.api}/district?region={region['slug']}", callback=self.parse_districts)

    def parse_districts(self, response: Response, **kwargs: Any) -> Any:
        for district in response.json()["data"]:
            yield Request(url=f"{self.api}/stores?district={district['slug']}", callback=self.parse)

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Vodashop ", "")
        item["addr_full"] = location["location"]
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
