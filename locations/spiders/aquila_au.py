from locations.storefinders.stockinstore import StockInStoreSpider

class AquilaAUSpider(StockInStoreSpider):
    name = "aquila_au"
    item_attributes = {"brand": "Aquila", "brand_wikidata": "Q17985574"}
    api_site_id = "10049"
    api_widget_id = "56"
    api_widget_type = "sis"
    api_origin = "https://www.aquila.com.au"
