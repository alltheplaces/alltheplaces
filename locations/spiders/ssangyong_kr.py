from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

SSANGYONG_SHARED_ATTRIBUTES = {"brand": "SsangYong", "brand_wikidata": "Q221869"}


class SsangyongKRSpider(JSONBlobSpider):
    name = "ssangyong_kr"
    item_attributes = SSANGYONG_SHARED_ATTRIBUTES
    allowed_domains = ["web.kg-mobility.com"]
    start_urls = ["https://web.kg-mobility.com/app/network/getDispBrchList.do?pageIdx=1&rowsPerPage=99999&range=50000&schTxt=&xCode=127.11768&yCode=37.466784"]
    locations_key = ["body", "dispBrchListInfo"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("shopCode")
        item["branch"] = feature.get("shopName")
        item["lat"] = feature.get("ycode")
        item["lon"] = feature.get("xcode")
        apply_category(Categories.SHOP_CAR, item)
        yield item
