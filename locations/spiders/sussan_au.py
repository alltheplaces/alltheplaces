from locations.storefinders.stockinstore import StockInStoreSpider


class SussanAUSpider(StockInStoreSpider):
    name = "sussan_au"
    item_attributes = {"brand": "Sussan", "brand_wikidata": "Q28184460"}
    api_site_id = "10051"
    api_widget_id = "58"
    api_widget_type = "product"
    api_origin = "https://www.sussan.com.au"
