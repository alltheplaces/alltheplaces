import re

import chompjs

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class RochesterZASpider(JSONBlobSpider):
    name = "rochester_za"
    item_attributes = {"brand": "Rochester", "brand_wikidata": "Q130377132"}
    start_urls = ["https://www.rochester.co.za/storelocator/"]

    def extract_json(self, response):
        data_raw = response.xpath(
            '//script[@type="text/x-magento-init"][contains(text(), "storelocator-store-list")]/text()'
        ).get()
        return chompjs.parse_js_object(data_raw)["#storelocator-store-list"]["Magento_Ui/js/core/app"]["components"][
            "storelocatorList"
        ]["storeData"]

    def post_process_item(self, item, response, location):
        if location["virtual_store"] == "1" or location["store_closed"] == "1":
            return
        item["branch"] = re.sub(r"rochester\s?-?\s?", "", item["name"], flags=re.IGNORECASE)
        item["website"] = f"https://www.rochester.co.za/storelocator/store/index/id/{item['ref']}"
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
