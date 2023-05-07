from locations.storefinders.stockinstore import StockInStoreSpider


class ZOMPAUSpider(StockInStoreSpider):
    name = "zomp_au"
    item_attributes = {"brand": "ZOMP", "brand_wikidata": "Q117747772"}
    api_site_id = "10121"
    api_widget_id = "128"
    api_widget_type = "product"
    api_origin = "https://zomp.com.au"
