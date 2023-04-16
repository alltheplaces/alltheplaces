from locations.storefinders.stockinstore import StockInStoreSpider


class TheNorthFaceAUNZSpider(StockInStoreSpider):
    name = "the_north_face_au_nz"
    item_attributes = {"brand": "The North Face", "brand_wikidata": "Q152784"}
    api_site_id = "10063"
    api_widget_id = "70"
    api_widget_type = "sis"
    api_origin = "https://thenorthface.com.au"
