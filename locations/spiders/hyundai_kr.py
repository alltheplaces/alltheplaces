from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

HYUNDAI_SHARED_ATTRIBUTES = {"brand": "Hyundai", "brand_wikidata": "Q55931"}


class HyundaiKRSpider(JSONBlobSpider):
    name = "hyundai_kr"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/kr/ko/gw/customer-support/v1/purchase-guide/agencies?latitude=37.486219&longitude=127.033676&mapLatitude=37.486219&mapLongitude=127.033676&radius=10000&pageSize=10000&pageNo=1&searchFilter=&agencyTypeCode=&deliveryAreaCode=&localAreaCode=&findType="]
    locations_key = ["data", "list"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["agencyCode"]
        item["branch"] = feature["agencyName"]
        item["addr_full"] = feature["agencyAddress"]
        item["phone"] = feature["agencyTel"]
        item["lat"] = feature["lattitude"]
        apply_category(Categories.SHOP_CAR, item)
        yield item
