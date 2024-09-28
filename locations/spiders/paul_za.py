from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES
from locations.storefinders.yext_search import YextSearchSpider


class PaulZASpider(YextSearchSpider):
    name = "paul_za"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    host = "https://location.paulsa.co.za"

    def parse_item(self, location, item):
        item["website"] = location["profile"]["c_pagesURL"]
        yield item
