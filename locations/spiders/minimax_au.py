from locations.storefinders.stockinstore import StockInStoreSpider

class MinimaxAUSpider(StockInStoreSpider):
    name = "minimax_au"
    item_attributes = {"brand": "Minimax", "brand_wikidata": "Q117747075"}
    api_site_id = "10081"
    api_widget_id = "88"
    api_widget_type = "cnc"
    api_origin = "https://www.minimax.com.au"
