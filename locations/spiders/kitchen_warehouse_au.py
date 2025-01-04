from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class KitchenWarehouseAUSpider(JSONBlobSpider):
    name = "kitchen_warehouse_au"
    item_attributes = {"brand": "Kitchen Warehouse", "brand_wikidata": "Q63603149"}
    allowed_domains = ["kwh-kitchenwarehouse.frontastic.live"]
    start_urls = ["https://kwh-kitchenwarehouse.frontastic.live/frontastic/action/storelocator/getstatewisestores"]

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url="https://kwh-kitchenwarehouse.frontastic.live/frontastic/action/ct-auth/getAnonymousAccessToken", method="POST", callback=self.parse_access_token)

    def parse_access_token(self, response: Response) -> Iterable[JsonRequest]:
        access_token = response.json()["access_token"]
        data = {
            "customer_reference": "",
            "skipIntrospection": True,
            "token": f"Bearer {access_token}",
        }
        yield JsonRequest(url=self.start_urls[0], data=data, meta={"access_token": access_token}, method="POST")

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
        access_token = response.meta["access_token"]
        data = {
            "customer_reference": "",
            "key": item["ref"],
            "skipIntrospection": True,
            "token": f"Bearer {access_token}",
        }
        yield JsonRequest(url="https://kwh-kitchenwarehouse.frontastic.live/frontastic/action/storelocator/storedetail", data=data, meta={"item": item}, method="POST", callback=self.add_opening_hours)

    def add_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        for day_hours in response.json()["storeHours"]:
            if day_hours["day"] not in DAYS_EN:
                continue
            item["opening_hours"].add_range(DAYS_EN[day_hours["day"]], day_hours["openTime"].replace(" ", ""), day_hours["closeTime"].replace(" ", ""), "%I.%M%p")
        yield item
