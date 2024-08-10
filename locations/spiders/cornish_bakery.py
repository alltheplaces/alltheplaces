from locations.storefinders.stockist import StockistSpider


class CornishBakerySpider(StockistSpider):
    name = "cornish_bakery"
    item_attributes = {
        "brand_wikidata": "Q124030035",
        "brand": "Cornish Bakery",
    }
    key = "u10286"
