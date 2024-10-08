from locations.storefinders.stockinstore import StockInStoreSpider


class T2AUSpider(StockInStoreSpider):
    name = "t2_au"
    item_attributes = {"brand": "T2", "brand_wikidata": "Q48802134"}
    api_site_id = "10024"
    api_widget_id = "31"
    api_widget_type = "sis"
    api_origin = "https://www.t2tea.com"
