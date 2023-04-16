from locations.storefinders.stockinstore import StockInStoreSpider

class ColetteByColetteHaymanAUSpider(StockInStoreSpider):
    name = "colette_by_colette_hayman_au"
    item_attributes = {"brand": "Colette by Colette Hayman", "brand_wikidata": "Q117746003"}
    api_site_id = "10066"
    api_widget_id = "73"
    api_widget_type = "cnc"
    api_origin = "https://www.colettehayman.com.au"
