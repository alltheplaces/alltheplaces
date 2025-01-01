import chompjs

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCYSpider(JSONBlobSpider):
    name = "burger_king_cy"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.com.cy/locations"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "initAreas([{")]/text()').get())

    def post_process_item(self, item, response, location):
        item["ref"] = location["nid"]
        item["branch"] = item.pop("name").replace("Burger King ", "")
        item["street_address"] = item.pop("street")
        yield item
