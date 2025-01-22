import json
from typing import Iterable

from scrapy import FormRequest, Request
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class BurgerKingKRSpider(JSONBlobSpider):
    download_timeout = 60
    name = "burger_king_kr"
    item_attributes = {"brand_wikidata": "Q177054"}
    locations_key = ["body", "storInfo"]

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        yield FormRequest(
            url="https://www.burgerking.co.kr/burgerking/BKR0343.json",
            headers={"accept": "*/*"},
            formdata={
                "message": json.dumps(
                    {
                        "header": {
                            "result": True,
                            "error_code": "",
                            "error_text": "",
                            "info_text": "",
                            "message_version": "",
                            "login_session_id": "",
                            "trcode": "BKR0343",
                            "cd_call_chnn": "01",
                        },
                        "body": {
                            "dataCount": "2000",
                            "membershipYn": "",
                            "orderType": "01",
                            "page": "1",
                            "searchKeyword": "",
                            "serviceCode": [],
                            "sort": "02",
                            "yCoordinates": "37.5726506",
                            "xCoordinates": "126.9810922",
                            "isAllYn": "Y",
                        },
                    }
                )
            },
        )

    def post_process_item(self, item, response, location):
        item["ref"] = location["storCd"]
        item["lat"] = location["storCoordY"]
        item["lon"] = location["storCoordX"]
        item["branch"] = location["storNm"]
        item["addr_full"] = location["storAddr"]
        item["phone"] = location["storTelNo"]
        if services := location.get("storeServiceCodeList"):
            services = [service["storeServiceName"] for service in services]
            apply_yes_no(Extras.DRIVE_THROUGH, item, "드라이브스루" in services, False)
            apply_yes_no(Extras.DELIVERY, item, "딜리버리" in services, False)

        item["opening_hours"] = OpeningHours()
        for days_key, days_val in [("storTimeDays", DAYS_WEEKDAY), ("storTimeWeekend", DAYS_WEEKEND)]:
            item["opening_hours"].add_days_range(days_val, *location[days_key].split("~"))
        yield item
