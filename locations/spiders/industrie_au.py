from locations.storefinders.stockinstore import StockInStoreSpider


class IndustrieAUSpider(StockInStoreSpider):
    name = "industrie_au"
    item_attributes = {"brand": "Industrie", "brand_wikidata": "Q117746099"}
    api_site_id = "10102"
    api_widget_id = "109"
    api_widget_type = "sis"
    api_origin = "https://www.industrie.com.au"
