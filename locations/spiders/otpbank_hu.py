from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class OtpbankHUSpider(Spider):
    name = "otpbank_hu"
    item_attributes = {"brand_wikidata": "Q912778"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.otpbank.hu/apps2/branch-atm-locator/atm/list",
            data={"enclosingRectangle": [{"latitude": 90, "longitude": 180}, {"latitude": -90, "longitude": -180}]},
        )
        yield JsonRequest(
            url="https://www.otpbank.hu/apps2/branch-atm-locator/branch/list",
            data={"enclosingRectangle": [{"latitude": 90, "longitude": 180}, {"latitude": -90, "longitude": -180}]},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        is_atm = "branch-atm-locator/atm/list" in response.url
        for location in response.json():
            item = Feature()
            item["ref"] = location["id"]
            item["addr_full"] = location["address"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]

            if is_atm:
                item["opening_hours"] = "24/7" if location["openingHours"] == "AVAILABLE_7_24" else None
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)

            yield item
