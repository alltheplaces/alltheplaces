import chompjs

from locations.items import get_merged_item
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingVNSpider(JSONBlobSpider):
    name = "burger_king_vn"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.vn/storepickup?___store=en", "https://burgerking.vn/storepickup?___store=vn"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    stored_items = {}

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var listStoreJson = ")]/text()').get()
        )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("BURGER KING ", "")
        item.pop("state")
        item.pop("city")
        if item["email"] == "test@gmail.com":
            item.pop("email")
        item["website"] = location["store_view_url"]
        if item["ref"] in self.stored_items:
            other_item = self.stored_items[item["ref"]]
            if response.url.endswith("en"):
                yield get_merged_item({"en": item, "vn": other_item}, "vn")
            else:
                yield get_merged_item({"en": other_item, "vn": item}, "vn")
        else:
            self.stored_items[item["ref"]] = item
