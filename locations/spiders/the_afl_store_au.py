from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class TheAflStoreAUSpider(StockistSpider):
    name = "the_afl_store_au"
    item_attributes = {"brand": "The AFL Store", "brand_wikidata": "Q117851311", "extras": Categories.SHOP_SPORTS.value}
    key = "u15982"

    def parse_item(self, item, location):
        for field in location["custom_fields"]:
            if field["name"] == "Store Details":
                item["website"] = field["value"]
                break
        yield item
