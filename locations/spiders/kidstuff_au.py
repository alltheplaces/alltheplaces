from locations.storefinders.stockinstore import StockInStoreSpider


class KidstuffAUSpider(StockInStoreSpider):
    name = "kidstuff_au"
    item_attributes = {"brand": "Kidstuff", "brand_wikidata": "Q117746407"}
    api_site_id = "10041"
    api_widget_id = "48"
    api_widget_type = "cnc"
    api_origin = "https://www.kidstuff.com.au"
