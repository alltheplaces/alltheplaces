from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class GautrainZASpider(JSONBlobSpider):
    name = "gautrain_za"
    item_attributes = {
        "operator": "Gautrain",
        "operator_wikidata": "Q1476881",
    }
    start_urls = ["https://www.gautrain.co.za/commuter/stations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # redirects to login page

    def post_process_item(self, item, response, location):
        if "Rail" in location["modes"]:
            apply_category(Categories.TRAIN_STATION, item)
            yield item
