import chompjs

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingIESpider(JSONBlobSpider):
    name = "burger_king_ie"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.whopper.ie/locations/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var markers = ")]/text()').get())

    def post_process_item(self, item, response, location):
        item["ref"] = location["place_id"]
        yield item
