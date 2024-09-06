import chompjs

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class SleepmastersSpider(JSONBlobSpider):
    name = "sleepmasters"
    item_attributes = {"brand": "Sleepmasters", "brand_wikidata": "Q116475002"}
    start_urls = ["https://www.sleepmasters.co.za/storelocator/"]

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
        item["branch"] = item.pop("name")
        item["website"] = f"https://www.sleepmasters.co.za/storelocator/store/index/id/{item['ref']}"
        item["country"] = location["country_id"]
        item["opening_hours"] = OpeningHours()
        days = {}
        try:
            days = chompjs.parse_js_object(location["opening_hours"]).values()
        except AttributeError:
            try:
                days = chompjs.parse_js_object(location["opening_hours"])
            except AttributeError:
                pass
        if days != {}:
            for day in days:
                try:
                    item["opening_hours"].add_range(day["weekday"], day["open_time"], day["close_time"])
                except ValueError:
                    pass
        yield item
