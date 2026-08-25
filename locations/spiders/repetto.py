from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class RepettoSpider(JSONBlobSpider):
    name = "repetto"
    item_attributes = {
        "brand": "Repetto",
        "brand_wikidata": "Q3427237",
    }
    start_urls = ["https://xnkosumdt5.execute-api.eu-west-3.amazonaws.com/prod/getStoreLocators"]

    def post_process_item(self, item, response, location):
        item["ref"] = item.get("name")
        item["branch"] = item.pop("name", "")
        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
