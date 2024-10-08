from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class IntersportAUSpider(StockInStoreSpider):
    name = "intersport_au"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888", "extras": Categories.SHOP_SPORTS.value}
    api_site_id = "10208"
    api_widget_id = "212"
    api_widget_type = "storelocator"
    api_origin = "https://intersport.com.au"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        item["website"] = "https://intersport.com.au" + item["website"]
        yield item
