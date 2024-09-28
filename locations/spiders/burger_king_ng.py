from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES

ORDERS_MAP = {
    "OrderTypeDelivery": Extras.DELIVERY,
    "OrderTypeTakeOut": Extras.TAKEAWAY,
}


class BurgerKingNGSpider(JSONBlobSpider):
    name = "burger_king_ng"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://api-mena.menu.app/api/directory/search"]
    locations_key = ["data", "venues", "data"]
    website_root = "https://www.burger-king.ng/restaurants/"
    request_headers = {"application": "5a426f83bbd4be2eb694497c5700c743"}
    request_data = {"latitude": "0", "longitude": "0", "order_types": [4, 6], "view": "search", "per_page": 50}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers=self.request_headers,
                data=self.request_data,
            )

    def parse(self, response):
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        if next_page := response.json()["data"]["venues"].get("next_page_url"):
            yield JsonRequest(
                url=next_page,
                headers=self.request_headers,
                data=self.request_data,
            )

    def pre_process_data(self, feature: dict) -> None:
        for key, value in feature["venue"].items():
            feature[key] = value

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item.pop("state")
        if "addr_full" in item:
            item["street_address"] = item.pop("addr_full")
        if address := item["street_address"]:
            slug = address.replace(" ", "-").replace(",", "").lower()
        else:
            slug = "no-address"
        item["website"] = f"{self.website_root}{slug}?id={item['ref']}"

        orders = [order["reference_type"] for order in location["order_types"]]
        for order in orders:
            if tag := ORDERS_MAP.get(order):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_order_type/{order}")

        item["opening_hours"] = OpeningHours()
        for rule in location["serving_times"]:
            if rule["type_id"] != 2:
                continue
            for day in rule["days"]:
                if rule["time_from"] == "00:00" and rule["time_to"] == "00:00":
                    item["opening_hours"].add_range(DAYS[day - 1], "00:00", "23:59")
                else:
                    item["opening_hours"].add_range(DAYS[day - 1], rule["time_from"], rule["time_to"])

        yield item
