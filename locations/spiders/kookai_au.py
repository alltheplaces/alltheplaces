from locations.storefinders.stockinstore import StockInStoreSpider


class KookaiAUSpider(StockInStoreSpider):
    name = "kookai_au"
    item_attributes = {"brand": "Kookaï", "brand_wikidata": "Q1783759"}
    api_site_id = "10003"
    api_widget_id = "11"
    api_widget_type = "sis"
    api_origin = "https://www.kookai.com.au"
