import json
from typing import Any, AsyncIterator, Iterable
from urllib.parse import quote

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingJPSpider(Spider):
    name = "burger_king_jp"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    page_size = 100

    def make_request(self, page: int) -> Request:
        message = {
            "header": {
                "result": True,
                "error_code": "",
                "error_text": "",
                "info_text": "",
                "message_version": "",
                "login_session_id": "",
                "trcode": "BKJ0302",
                "cdCallChnn": "02",
            },
            "body": {
                "tpSearchStore": "03",
                "searchKeyword": "",
                "storeServiceCode": [""],
                "sort": "02",
                "xCoordinates": "",
                "yCoordinates": "",
                "page": page,
                "dataCount": self.page_size,
            },
        }
        return Request(
            url="https://www.burgerking.co.jp/burgerking/BKJ0302.json",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
            body="message=" + quote(json.dumps(message, separators=(",", ":"))),
            cb_kwargs={"page": page},
            callback=self.parse,
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, page: int, **kwargs: Any) -> Iterable[Feature | Request]:
        body = response.json()["body"]
        for location in body["data"]:
            item = Feature()
            item["ref"] = location["storCd"]
            item["lat"] = location["storCoordY"]
            item["lon"] = location["storCoordX"]
            item["branch"] = location["storNm"]
            item["addr_full"] = location["storAddr"]
            item["website"] = "https://www.burgerking.co.jp/"
            services = {service["storeServiceCode"] for service in location.get("storeServiceCodeList") or []}
            apply_yes_no(Extras.DRIVE_THROUGH, item, "02" in services, False)
            apply_category(Categories.FAST_FOOD, item)
            yield item

        # The endpoint caps results per page; follow pages until the reported total is reached.
        if page * self.page_size < int(body["dataCount"]):
            yield self.make_request(page + 1)
