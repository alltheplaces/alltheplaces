from locations.storefinders.stockist import StockistSpider


class WallaceBishopAUSpider(StockistSpider):
    name = "wallace_bishop_au"
    item_attributes = {
        "brand_wikidata": "Q18636699",
        "brand": "Wallace Bishop",
    }
    key = "u8410"
