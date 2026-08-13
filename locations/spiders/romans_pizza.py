import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

API_ROOT = "https://ecommerce-api-alt-g2euc.ondigitalocean.app"
TENANT_HEADERS = {"Origin": "https://romanspizza.co.za"}


class RomansPizzaSpider(JSONBlobSpider):
    name = "romans_pizza"
    item_attributes = {"brand_wikidata": "Q65079427"}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"{API_ROOT}/api/client/storeTags/public/stores",
            method="POST",
            headers=TENANT_HEADERS,
            data={"channelType": "WEBSITE", "tagGroupItemIds": []},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature.pop("uuid")
        feature.update(feature.pop("location"))
        address = feature.pop("addressInfo", {})
        address.pop("id", None)
        address["street_address"] = merge_address_lines(
            [address.pop("shopNumber", None), address.pop("buildingName", None), address.pop("streetAddress", None)]
        )
        address["state"] = address.pop("province", None)
        feature.update(address)
        feature["phone"] = "; ".join(p for p in feature.pop("phoneNumbers", None) or [] if p and p != "0")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Request]:
        item["branch"] = re.sub(r"^Roman[`'’]?s Pizza\s*", "", item.pop("name") or "").strip()
        item["website"] = f"https://romanspizza.co.za/store-locator/{item['ref']}"
        yield Request(
            url=f"{API_ROOT}/api/customer/store/withDetails/{item['ref']}",
            headers=TENANT_HEADERS,
            callback=self.parse_hours,
            errback=self.parse_hours_error,
            cb_kwargs={"item": item},
        )

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day in response.json().get("TradingHours") or []:
            if day.get("is24Hours"):
                item["opening_hours"].add_range(day["dayOfWeek"], "00:00", "23:59")
            elif not day.get("open"):
                item["opening_hours"].set_closed(day["dayOfWeek"])
            else:
                for timing in day.get("storeTiming") or []:
                    open_time, _, close_time = timing.partition(" - ")
                    item["opening_hours"].add_range(day["dayOfWeek"], open_time.strip(), close_time.strip())
        yield item

    def parse_hours_error(self, failure) -> Iterable[Feature]:
        yield failure.request.cb_kwargs["item"]
