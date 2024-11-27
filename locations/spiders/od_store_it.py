from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class OdStoreITSpider(JSONBlobSpider):
    name = "od_store_it"
    item_attributes = {
        "brand": "ODStore",
        "brand_wikidata": "Q130492509",
        "extras": Categories.SHOP_CONFECTIONERY.value,
    }
    start_urls = ["https://odstore.it/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1&layout=1"]

    def post_process_item(self, item, response, location):
        item["extras"]["addr:province"] = item.pop("state")
        item["street_address"] = item.pop("street")
        item["branch"] = item.pop("name")
        item["name"] = "ODStore"
        yield item
