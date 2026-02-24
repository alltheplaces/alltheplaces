from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES


class ForeverNewINSpider(JSONBlobSpider):
    name = "forever_new_in"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    start_urls = ["https://www.forevernew.co.in/mpstorelocator/storelocator/locationsdata/"]
    needs_json_request = True
    requires_proxy = True

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("Forever New - ", "")
        item.pop("street")
        item.pop("website")
        yield item
