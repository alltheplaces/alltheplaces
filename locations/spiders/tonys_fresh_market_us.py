from locations.categories import Categories
from locations.storefinders.freshop import FreshopSpider


class TonysFreshMarketUSSpider(FreshopSpider):
    name = "tonys_fresh_market_us"
    item_attributes = {
        "brand": "Tony's Fresh Market",
        "brand_wikidata": "Q118594253",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    app_key = "tony_s_fresh_market"

    def parse_item(self, item, location):
        item["phone"] = item["phone"].split("\n", 1)[0]
        yield item
