from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class IcelandFoodsSpider(Spider):
    name = "iceland_foods"
    item_attributes = {"brand": "Iceland", "brand_wikidata": "Q721810"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    access_token = ""

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.iceland.co.uk/mobify/proxy/ocapi/on/demandware.store/Sites-icelandfoodsuk-Site/default/Account-GetAccessToken",
            data={},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.access_token = response.json()["access_token"]
        yield JsonRequest(
            url="https://prd.cc-iceland.co.uk/s/icelandfoodsuk/dw/shop/v22_6/stores?count=200&start=0&distance_unit=mi&max_distance=500&latitude=51.5072178&longitude=-0.1275862",
            headers={"authorization": f"Bearer {self.access_token}"},
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            item = DictParser.parse(store)

            item["branch"] = item.pop("name")
            if "FWH" in item["branch"] or "Food Ware" in item["branch"]:
                # The Food Warehouse, obtained via its own spider
                # The name usually ends with FWH or has Food Warehouse, sometime truncated.
                continue

            item["street_address"] = merge_address_lines([store.get("address1"), store.get("address2")])
            item["state"] = store.get("c_storeRegion")

            if "IRELAND" in item["branch"]:
                item["country"] = "IE"
            else:
                item["country"] = "GB"

            yield item

        if next_page := response.json().get("next"):
            yield JsonRequest(
                url=next_page, headers={"authorization": f"Bearer {self.access_token}"}, callback=self.parse_stores
            )
