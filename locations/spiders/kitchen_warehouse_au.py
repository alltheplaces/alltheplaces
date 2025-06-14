from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class KitchenWarehouseAUSpider(JSONBlobSpider):
    name = "kitchen_warehouse_au"
    item_attributes = {"brand": "Kitchen Warehouse", "brand_wikidata": "Q63603149"}
    allowed_domains = ["kwh-kitchenwarehouse.frontastic.live"]
    stores_api = "https://kwh-kitchenwarehouse.frontastic.live/frontastic/action"
    access_token = ""
    request_body = {}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url=f"{self.stores_api}/ct-auth/getAnonymousAccessToken",
            method="POST",
            callback=self.parse_access_token,
        )

    def parse_access_token(self, response: Response) -> Iterable[JsonRequest]:
        self.access_token = response.json()["access_token"]
        self.request_body = {
            "customer_reference": "",
            "skipIntrospection": True,
            "token": f"Bearer {self.access_token}",
            "isAnonymousUser": True,
        }
        yield JsonRequest(
            url=f"{self.stores_api}/storelocator/getstatewisestores", data=self.request_body, method="POST"
        )

    def extract_json(self, response: Response) -> list[dict]:
        all_stores = []
        for state in response.json():
            for store in state["stores"]:
                all_stores.append(store)
        return all_stores

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[JsonRequest]:
        item["ref"] = feature.get("key")
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        item["website"] = "https://www.kitchenwarehouse.com.au/find-store/" + item["branch"].lower().replace(" ", "-")
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield JsonRequest(
            url=f"{self.stores_api}/storelocator/storedetail",
            data=self.request_body | {"key": item["ref"]},
            meta={"item": item},
            method="POST",
            callback=self.add_opening_hours,
        )

    def add_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        try:
            item["opening_hours"] = OpeningHours()
            for day_hours in response.json().get("storeHours", []):
                if day := sanitise_day(day_hours.get("day")):
                    item["opening_hours"].add_range(
                        day, day_hours["openTime"].replace(" ", ""), day_hours["closeTime"].replace(" ", ""), "%I.%M%p"
                    )
        except:
            item["opening_hours"] = None
            self.logger.error(f'Error parsing opening hours: {response.json().get("storeHours", [])}')
        yield item
