from locations.storefinders.stockist import StockistSpider


class CornishBakeryGBSpider(StockistSpider):
    name = "cornish_bakery_gb"
    item_attributes = {
        "brand_wikidata": "Q124030035",
        "brand": "Cornish Bakery",
    }
    key = "u10286"
