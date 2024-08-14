from locations.storefinders.stockist import StockistSpider


class TedBakerUSSpider(StockistSpider):
    name = "ted_baker_us"
    item_attributes = {
        "brand_wikidata": "Q2913458",
        "brand": "Ted Baker",
    }
    key = "u18638"
