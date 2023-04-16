from locations.storefinders.stockinstore import StockInStoreSpider

class SuzanneGraeAUSpider(StockInStoreSpider):
    name = "suzanne_grae_au"
    item_attributes = {"brand": "Suzanne Grae", "brand_wikidata": "Q117747672"}
    api_site_id = "10052"
    api_widget_id = "59"
    api_widget_type = "cnc"
    api_origin = "https://www.suzannegrae.com.au"
