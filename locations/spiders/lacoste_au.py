from locations.storefinders.stockinstore import StockInStoreSpider

class LacosteAUSpider(StockInStoreSpider):
    name = "lacoste_au"
    item_attributes = {"brand": "Lacoste", "brand_wikidata": "Q309031"}
    api_site_id = "10055"
    api_widget_id = "62"
    api_widget_type = "sis"
    api_origin = "https://lacoste.com.au"
