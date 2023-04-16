from locations.storefinders.stockinstore import StockInStoreSpider

class EarlySettlerSpider(StockInStoreSpider):
    name = "early_settler"
    item_attributes = {"brand": "Early Settler", "brand_wikidata": "Q111080173"}
    api_site_id = "10014"
    api_widget_id = "22"
    api_widget_type = "storelocator"
    api_origin = "https://earlysettler.com.au"
