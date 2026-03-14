from locations.json_blob_spider import JSONBlobSpider


class DominosPizzaPKSpider(JSONBlobSpider):
    name = "dominos_pizza_pk"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.com.pk/api/customer/stores"]
    locations_key = "successResponse"

    def post_process_item(self, item, response, location):
        item["phone"] = location["contact1"]
        item["branch"] = item.pop("name")
        yield item
