import json
from typing import Any, AsyncIterator, Iterable

from scrapy import FormRequest
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FastrakZASpider(JSONBlobSpider):
    name = "fastrak_za"
    item_attributes = {
        "brand": "Fastrak",
        "brand_wikidata": "Q120799603",
    }
    locations_key = ["data", "mapData"]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            "https://msl.cirkleinc.com/api/Send-Records?page=1",
            formdata={"shop": "fastrak-sa.myshopify.com", "page": "1"},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("hash_code")
        feature["phone"] = feature.pop("phone_no")
        feature["postcode"] = feature.pop("pin_code")
        feature["lon"] = feature.pop("lng")

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("facebook", None)
        item.pop("website", None)
        item["branch"] = feature["store_name"].removeprefix("Fastrak:").strip()

        if raw := feature.get("open_hours"):
            oh = OpeningHours()
            for day, times in json.loads(raw).items():
                times = (times or "").strip()
                if not times:
                    continue
                if times.lower() == "closed":
                    oh.set_closed(DAYS[int(day) - 1])
                else:
                    oh.add_ranges_from_string(f"{DAYS[int(day) - 1]} {times}")
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_HIFI, item)
        yield item
