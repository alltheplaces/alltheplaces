from copy import deepcopy
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class HyundaiIDSpider(Spider):
    name = "hyundai_id"
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/wsvc/template_en/spa/common/dealer/list.html"]

    async def start(self) -> AsyncIterator[FormRequest]:
        headers = {
            "Accept": "application/json",
            "Referer": "https://www.hyundai.com/id/en/build-a-car/find-a-dealer",
            "X-Requested-With": "XMLHttpRequest",
        }
        formdata = {
            "loc": "ID",
            "lan": "en",
            "defalut_latitude": "-6.20278",  # Typo exists in source.
            "defalut_long": "106.84944",  # Typo exists in source.
            "distanceUnit": "K",
            "distanceValue": "100000",
            "dealerService": "241,242,321,322",
            "search_type": "E",
            "s_dealer_name": "",
            "s_dealer_post_code": "",
            "s_dealer_address": "",
            "searchDealerNum": "200",
            "search_word": "",
            "search_dealer_type": "D",
        }
        yield FormRequest(url=self.start_urls[0], method="POST", formdata=formdata, headers=headers)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json():
            item = Feature()
            item["ref"] = data.get("dealer_seq")
            item["branch"] = data.get("dealer_name").removeprefix("Hyundai ")
            item["lat"] = data.get("latitude")
            item["lon"] = data.get("longtitude")
            item["addr_full"] = data.get("dealer_address")
            item["postcode"] = data.get("dealer_post_code").removesuffix(".0")
            item["phone"] = data.get("dealer_phone1", "").removeprefix("Tel ")
            services = data.get("dealer_service_nm", "")
            has_showroom = "Sales" in services
            has_service = "Service and Spare Part" in services

            if has_showroom:
                sales_item = deepcopy(item)
                sales_item["ref"] = f"{item['ref']}-sales"
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item

            if has_service:
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
