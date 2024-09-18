from typing import Iterable

from scrapy.http import FormRequest

from locations.spiders.hyundai_th import HyundaiTHSpider


class HyundaiIDSpider(HyundaiTHSpider):
    name = "hyundai_id"
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/wsvc/template_en/spa/common/dealer/list.html"]

    def start_requests(self) -> Iterable[FormRequest]:
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
