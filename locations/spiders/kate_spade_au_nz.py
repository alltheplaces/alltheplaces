from locations.storefinders.stockinstore import StockInStoreSpider


class KateSpadeAUNZSpider(StockInStoreSpider):
    name = "kate_spade_au_nz"
    item_attributes = {"brand": "Kate Spade New York", "brand_wikidata": "Q6375797"}
    api_site_id = "10076"
    api_widget_id = "83"
    api_widget_type = "sis"
    api_origin = "https://katespade.com.au"
    custom_settings = {"ROBOTSTXT_OBEY": False}
