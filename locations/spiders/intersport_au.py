from locations.storefinders.stockinstore import StockInStoreSpider


class IntersportAUSpider(StockInStoreSpider):
    name = "intersport_au"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    api_site_id = "10004"
    api_widget_id = "12"
    api_widget_type = "cnc"
    api_origin = "https://intersport.com.au"
