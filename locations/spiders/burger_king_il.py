from chompjs import parse_js_object
from scrapy.http import Request

from locations.categories import Extras, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class BurgerKingILSpider(JSONBlobSpider):
    name = "burger_king_il"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerking.co.il/branch/"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def start_requests(self):
        headers = {
            "Sec-Ch-Ua-Platform": "Linux",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        for url in self.start_urls:
            yield Request(url=url, headers=headers)

    def extract_json(self, response):
        return parse_js_object(
            response.xpath("//script[contains(text(), '\"branches\":')]/text()").get().split('"branches":')[1]
        )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(" (כשר)", "").strip()

        # This does not work for all items, some have an extra word in the slug
        # slug = item["branch"].replace(" – ", " ").replace(" ", "-")
        # item["website"] = "https://www.burgerking.co.il/branch/" + slug

        apply_yes_no(Extras.KOSHER, item, location["icons_tags"]["is_kosher"] == 1)
        apply_yes_no(Extras.WIFI, item, location["icons_tags"]["is_wifi"] == 1)
        apply_yes_no(Extras.WHEELCHAIR, item, location["icons_tags"]["is_acc"] == 1)
        apply_yes_no(Extras.DELIVERY, item, location["icons_tags"]["can_ship"] == 1)
        yield item
        # TODO could parse hours from individual store pages, but they are in Hebrew
