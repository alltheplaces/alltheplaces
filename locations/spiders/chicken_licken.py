from locations.categories import Extras, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class ChickenLickenSpider(JSONBlobSpider):
    name = "chicken_licken"
    item_attributes = {"brand": "Chicken Licken", "brand_wikidata": "Q4164819"}
    start_urls = ["https://chickenlicken.co.za/api/stores"]

    def post_process_item(self, item, response, location):
        item["addr_full"] = " ".join([str(location["address"]), str(location["address2"]), str(location["area"])])
        apply_yes_no(Extras.DELIVERY, item, location["delivery"] == "1")
        yield item
