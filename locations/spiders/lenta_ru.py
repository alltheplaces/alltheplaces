import json
import uuid
from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class LentaRUSpider(Spider):
    name = "lenta_ru"
    item_attributes = {"brand": "Лента", "brand_wikidata": "Q4258608"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    allowed_domains = ["lenta.com"]
    device_id = str(uuid.uuid4())

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://lenta.com/api/rest/sessionGet",
            headers={"x-retail-brand": "lo"},
            formdata={
                "request": json.dumps(
                    {
                        "Head": {
                            "MarketingPartnerKey": "mp300-b1de0bac2c257f3257bf5ef2eea4ecbc",
                            "Method": "sessionGet",
                            "DeviceId": self.device_id,
                        },
                        "Body": {},
                    }
                ),
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://lenta.com/api-gateway/v1/stores/pickup/search",
            headers={
                "deviceid": self.device_id,
                "sessiontoken": response.json()["Body"]["SessionToken"],
                "x-retail-brand": "lo",
                "x-platform": "omniweb",
            },
            data={},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item.pop("name")
            item["addr_full"] = location["addressFull"]
            item["opening_hours"] = self.parse_opening_hours(location["storeWorkingHours"])

            if location.get("marketType") == "ZO":
                apply_category(Categories.SHOP_PET, item)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)

            apply_yes_no(Extras.TAKEAWAY, item, "PICKUP" in location["features"])
            yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        oh.add_days_range(DAYS, opening_hours.get("open"), opening_hours.get("close"))
        return oh
