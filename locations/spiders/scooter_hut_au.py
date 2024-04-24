from locations.storefinders.stockinstore import StockInStoreSpider


class ScooterHutAUSpider(StockInStoreSpider):
    name = "scooter_hut_au"
    item_attributes = {"brand": "Scooter Hut", "brand_wikidata": "Q117747623", "extras": {"shop": "scooter"}}
    api_site_id = "10112"
    api_widget_id = "119"
    api_widget_type = "product"
    api_origin = "https://scooterhut.com.au"
