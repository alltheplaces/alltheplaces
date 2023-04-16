from locations.storefinders.stockinstore import StockInStoreSpider

class MassiveJoesAUSpider(StockInStoreSpider):
    name = "massivejoes_au"
    item_attributes = {"brand": "MassiveJoes", "brand_wikidata": "Q117746887"}
    api_site_id = "10091"
    api_widget_id = "98"
    api_widget_type = "sis"
    api_origin = "https://massivejoes.com"
