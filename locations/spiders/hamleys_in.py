import re

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hamleys import HAMLEYS_SHARED_ATTRIBUTES


class HamleysINSpider(JSONBlobSpider):
    name = "hamleys_in"
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES
    start_urls = ["https://hmpim.hamleys.in/pim/pimresponse.php?service=storelocator"]
    locations_key = "result"

    def post_process_item(self, item, response, location):
        item["branch"] = re.sub(r"^hamleys\s?-?_?\s?", "", item.pop("name"), flags=re.IGNORECASE)
        yield item
