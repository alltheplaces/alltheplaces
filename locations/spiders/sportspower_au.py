from locations.storefinders.stockinstore import StockInStoreSpider


class SportspowerAUSpider(StockInStoreSpider):
    name = "sportspower_au"
    item_attributes = {"brand": "SportsPower", "brand_wikidata": "Q117747652"}
    api_site_id = "10067"
    api_widget_id = "74"
    api_widget_type = "storelocator"
    api_origin = "https://www.sportspower.com.au"
