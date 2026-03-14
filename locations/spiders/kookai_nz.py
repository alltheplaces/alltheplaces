from locations.storefinders.stockinstore import StockInStoreSpider


class KookaiNZSpider(StockInStoreSpider):
    name = "kookai_nz"
    item_attributes = {"brand": "Kookaï", "brand_wikidata": "Q1783759"}
    api_site_id = "10006"
    api_widget_id = "14"
    api_widget_type = "product"
    api_origin = "https://www.kookai.co.nz"
