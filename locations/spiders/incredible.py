import chompjs

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class IncredibleSpider(JSONBlobSpider):
    name = "incredible"
    item_attributes = {"brand": "Incredible", "brand_wikidata": "Q130377046"}
    start_urls = ["https://www.incredible.co.za/storelocator"]

    def extract_json(self, response):
        data_raw = response.xpath(
            '//script[@type="text/x-magento-init"][contains(text(), "storelocator-store-list")]/text()'
        ).get()
        return chompjs.parse_js_object(data_raw)["#storelocator-store-list"]["Magento_Ui/js/core/app"]["components"][
            "storelocatorList"
        ]["storeData"]

    def post_process_item(self, item, response, location):
        if item["name"].lower().endswith("cellular"):
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
        if location["virtual_store"] == "1" or location["store_closed"] == "1":
            return
        item["branch"] = item.pop("name").replace(" INCREDIBLE CONNECTION", "")
        item["website"] = f"https://www.incredible.co.za/storelocator/store/index/id/{item['ref']}"
        item["country"] = location["country_id"]
        item["opening_hours"] = OpeningHours()
        try:
            for day in chompjs.parse_js_object(location["opening_hours"]).values():
                try:
                    item["opening_hours"].add_range(day["weekday"], day["open_time"], day["close_time"])
                except ValueError:
                    pass
        except AttributeError:
            pass
        yield item
