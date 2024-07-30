from locations.storefinders.stockist import StockistSpider


class TedBakerSpider(StockistSpider):
    name = "ted_baker"
    item_attributes = {
        "brand_wikidata": "Q2913458",
        "brand": "Ted Baker",
    }
    key = "u18638"
