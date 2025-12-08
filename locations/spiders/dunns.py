from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class DunnsSpider(JSONBlobSpider):
    name = "dunns"
    item_attributes = {"brand": "Dunns", "brand_wikidata": "Q116619823"}
    start_urls = ["https://store-locator-shopify-app-d9f525452f2f.herokuapp.com/api/stores?brand=Dunns"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["ref"] = feature["_id"]
        oh = OpeningHours()
        for day, time in feature["operating_hours"].items():
            if day.title() in DAYS_FULL:
                oh.add_range(day, time["open"], time["close"], time_format="%H:%M:%S")
            item["opening_hours"] = oh

        yield item
