from locations.storefinders.stockinstore import StockInStoreSpider

class SportsgirlAUSpider(StockInStoreSpider):
    name = "sportsgirl_au"
    item_attributes = {"brand": "Sportsgirl", "brand_wikidata": "Q7579970"}
    api_site_id = "10047"
    api_widget_id = "54"
    api_widget_type = "cnc"
    api_origin = "https://www.sportsgirl.com.au"
