from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PizzaPerfectZASpider(WPStoreLocatorSpider):
    name = "pizza_perfect_za"
    item_attributes = {
        "brand_wikidata": "Q116619227",
        "brand": "Pizza Perfect",
    }
    allowed_domains = [
        "pizzaperfect.co.za",
    ]
    max_results = 100
    iseadgg_countries_list = ["ZA"]
    search_radius = 50
    days = DAYS_EN
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item.pop("addr_full", None)
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("Pizza Perfect ")
        item["phone"] = item["phone"].split("/")[0].split("|")[0]
        yield item
