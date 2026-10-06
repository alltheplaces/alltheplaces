from locations.categories import Categories, apply_category
from locations.storefinders.freshop import FreshopSpider


class TonysFreshMarketUSSpider(FreshopSpider):
    name = "tonys_fresh_market_us"
    item_attributes = {"brand": "Tony's Fresh Market", "brand_wikidata": "Q118594253"}
    app_key = "tony_s_fresh_market"

    def parse_item(self, item, location):
        item["phone"] = item["phone"].split("\n", 1)[0]
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
