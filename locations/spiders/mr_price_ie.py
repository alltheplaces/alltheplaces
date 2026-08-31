import re
from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MrPriceIESpider(JSONBlobSpider):
    name = "mr_price_ie"
    item_attributes = {"brand": "Mr. Price", "brand_wikidata": "Q113197454"}
    locations_key = "locations"

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://stores.mrprice.ie/stores/stores_result",
            formdata={"radius": "500", "latitude": "53.33", "longitude": "-7.77"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("location_id")
        feature["name"] = feature.pop("location_title")
        feature["address"] = feature.pop("location_address")
        feature["phone"] = feature.pop("location_telephone")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^Mr\s?PRICE\s+", "", item.pop("name"), flags=re.IGNORECASE)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
