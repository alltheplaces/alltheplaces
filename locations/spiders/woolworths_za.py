import re

from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.json_blob_spider import JSONBlobSpider


class WoolworthsZASpider(JSONBlobSpider):
    name = "woolworths_za"
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q8033997"}
    locations_key = "stores"

    def start_requests(self):
        yield JsonRequest(
            url="https://www.woolworths.co.za/server/storelocatorByArea?suburbId=3041&distance=100000",
            headers={"Referer": "https://www.woolworths.co.za/storelocator"},
        )

    def post_process_item(self, item, response, store):
        item["street_address"] = store.get("storeAddressInfo")
        item["addr_full"] = store.get("storeAddress")
        timing = store.get("openingHours")
        if all("closed" in t.get("hours", "").lower() for t in timing):
            return
        item["opening_hours"] = OpeningHours()
        for rule in timing:
            if day := sanitise_day(rule.get("day")):
                for open_time, close_time in re.findall(
                    r"(\d+:\d+)[-\s]+(\d+:\d+)", rule.get("hours", "").replace("h", ":")
                ):
                    item["opening_hours"].add_range(day, open_time, close_time)

        if len(store.get("departments", [])) == 1:
            if "Food" in store["departments"][0]:
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif "Clothing" in store["departments"][0]:
                apply_category(Categories.SHOP_CLOTHES, item)
            else:
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        else:
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
