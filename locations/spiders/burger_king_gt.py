from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingGTSpider(JSONBlobSpider):
    name = "burger_king_gt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://bk.gt/mas-cerca-de-ti"]

    def extract_json(self, response):
        return parse_js_object(
            response.xpath('//script[contains(text(), "var markers = ")]/text()')
            .get()
            .split("var markers = JSON.parse('")[1]
        )

    def post_process_item(self, item, response, location):
        item["ref"] = item["website"]
        item["branch"] = item.pop("name").replace("BK ", "")
        yield item
        # TODO some more info on individual pages, but html parsing
