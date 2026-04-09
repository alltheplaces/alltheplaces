import json
from typing import AsyncIterator, Iterable

from scrapy import FormRequest
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.subway import SubwaySpider


class SubwayKRSpider(JSONBlobSpider):
    name = "subway_kr"
    item_attributes = SubwaySpider.item_attributes
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    locations_key = "searchResult"

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.subway.co.kr/ajaxStoreSearch",
            formdata={
                "keyword": "",
                "page": "1",
                "pagination": json.dumps({"pageNo": 1, "itemCountPerPage": 1500, "displayPageNoCount": 1500}),
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("openYn") == "N":  # coming soon or not in operation
            return
        item["addr_full"] = merge_address_lines([feature.get("storAddr1"), feature.get("storAddr2")])
        if not item["addr_full"] or feature.get("lat") in ["0", ""]:
            return
        item["ref"] = feature.get("storCd")
        item["branch"] = feature.get("storNm")
        item["phone"] = feature.get("storTel")
        item["website"] = f'https://www.subway.co.kr/storeDetail?franchiseNo={feature.get("franchiseNo")}'
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["takeaway"] = "yes"
        yield item
