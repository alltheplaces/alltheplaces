from typing import Iterable

from scrapy.http import FormRequest, Response

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiTHSpider(JSONBlobSpider):
    name = "hyundai_th"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/wsvc/template_en/spa/common/dealer/list.html"]

    def start_requests(self) -> Iterable[FormRequest]:
        headers = {
            "Accept": "application/json",
            "Referer": "https://www.hyundai.com/th/th/build-a-car/find-a-dealer",
            "X-Requested-With": "XMLHttpRequest",
        }
        formdata = {
            "loc": "TH",
            "lan": "th",
            "defalut_latitude": "13.7194494",  # Typo exists in source.
            "defalut_long": "100.5852771",  # Typo exists in source.
            "distanceUnit": "K",
            "distanceValue": "100000",
            "dealerService": "382,441,383,384",
            "search_type": "E",
            "s_dealer_name": "",
            "s_dealer_post_code": "",
            "s_dealer_address": "",
            "searchDealerNum": "150",
            "search_word": "",
            "search_dealer_type": "D",
        }
        yield FormRequest(url=self.start_urls[0], method="POST", formdata=formdata, headers=headers)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("dealer_seq")
        item["branch"] = feature.get("dealer_name")
        item["lon"] = feature.get("longtitude")  # Typo exists in source.
        item["addr_full"] = feature.get("dealer_address")
        item["postcode"] = feature.get("dealer_post_code")
        item["phone"] = feature.get("dealer_phone1", "").removeprefix("Tel ")
        apply_category(Categories.SHOP_CAR, item)
        yield item
