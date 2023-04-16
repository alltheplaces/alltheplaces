from locations.storefinders.stockinstore import StockInStoreSpider

class TriumphSpider(StockInStoreSpider):
    name = "triumph"
    item_attributes = {"brand": "Triumph", "brand_wikidata": "Q671216"}
    api_site_id = "10113"
    api_widget_id = "120"
    api_widget_type = "storelocator"
    api_origin = "https://au.triumph.com"

    def parse_item(self, item, location):
        if "Triumph " not in item["name"]:
            return
        yield item
