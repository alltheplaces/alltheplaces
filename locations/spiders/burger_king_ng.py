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
    # no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers={"application": "5a426f83bbd4be2eb694497c5700c743"},
                data={"latitude": "0", "longitude": "0", "order_types": [4, 6], "view": "search", "per_page": 5000},
            )

    def pre_process_data(self, feature: dict) -> None:
        for key, value in feature["venue"].items():
            feature[key] = value

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item.pop("state")
        item["street_address"] = item.pop("addr_full")
        slug = item["street_address"].replace(" ", "-").replace(",", "").lower()
        item["website"] = f"https://www.burger-king.ng/restaurants/{slug}?id={item['ref']}"

        orders = [order["reference_type"] for order in location["order_types"]]
        for order in orders:
            if tag := ORDERS_MAP.get(order):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_order_type/{order}")

        item["opening_hours"] = OpeningHours()
        for times in location["serving_times"]:
            if times["reference_type"] == "WeekDays" and set(times["days"]) == set([i for i in range(7)]):
                for day in DAYS:
                    item["opening_hours"].add_range(day, times["time_from"], times["time_to"])
            elif times["reference_type"] not in ["SpecialDays"]:
                self.crawler.stats.inc_value(f"atp/{self.name}/hours_failed/{times['reference_type']}")
        yield item
