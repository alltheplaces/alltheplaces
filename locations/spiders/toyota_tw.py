from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_us import ToyotaUSSpider


class ToyotaTWSpider(JSONBlobSpider):
    name = "toyota_tw"
    item_attributes = ToyotaUSSpider.item_attributes
    start_urls = ["https://www.toyota.com.tw/api/location.ashx"]
    locations_key = "DATA"

    def post_process_item(self, item, response, location: dict):
        if location["TYPE"] == "1":
            item["ref"] = "-".join([location["KEY"], "Dealer"])
            apply_category(Categories.SHOP_CAR, item)
        elif location["TYPE"] == "2":
            item["ref"] = "-".join([location["KEY"], "Service"])
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
