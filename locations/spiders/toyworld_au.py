from locations.storefinders.stockinstore import StockInStoreSpider


class ToyworldAUSpider(StockInStoreSpider):
    name = "toyworld_au"
    item_attributes = {"brand": "Toyworld", "brand_wikidata": "Q95923071"}
    api_site_id = "10046"
    api_widget_id = "53"
    api_widget_type = "storelocator"
    api_origin = "https://www.toyworld.com.au"
