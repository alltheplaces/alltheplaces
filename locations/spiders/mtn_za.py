from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class MtnZASpider(JSONBlobSpider):
    name = "mtn_za"
    item_attributes = {
        "brand_wikidata": "Q1813361",
        "brand": "MTN",
    }
    start_urls = [
        "https://www.mtn.co.za/api/cms/v1/store-location/1725724280978268358/coverage-map-store-app?storeCount=10000&latitude=-29&longitude=24"
    ]

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        item["branch"] = item.pop("name").replace("MTN Store - ", "").replace("MTN Lite - ", "")
        item["street_address"] = clean_address([location["addressExtra"], location["streetAndNumber"]])
        item["website"] = "https://www.mtn.co.za/home/coverage/store/" + location["slug"]

        item["opening_hours"] = OpeningHours()
        for day_hours in location["openingHours"]:
            if day_hours["closed"]:
                item["opening_hours"].set_closed(DAYS[day_hours["dayOfWeek"] - 1])
            item["opening_hours"].add_range(DAYS[day_hours["dayOfWeek"] - 1], day_hours["from1"], day_hours["to1"])

        yield item
