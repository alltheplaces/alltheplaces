from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class PylonesSpider(JSONBlobSpider):
    name = "pylones"
    item_attributes = {"brand": "Pylones", "brand_wikidata": "Q24287146"}
    start_urls = ["https://www.pylones.com/it/pylones-negozi?ajax=1&p=1&all=1"]
    locations_key = ["data", "stores"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["name"] = "Pylones"
        apply_category(Categories.SHOP_GIFT, item)
        yield item
