from locations.storefinders.stockinstore import StockInStoreSpider

class ToyworldNZSpider(StockInStoreSpider):
    name = "toyworld_nz"
    item_attributes = {"brand": "Toyworld", "brand_wikidata": "Q95923071"}
    api_site_id = "10044"
    api_widget_id = "51"
    api_widget_type = "storelocator"
    api_origin = "https://www.toyworld.co.nz"
