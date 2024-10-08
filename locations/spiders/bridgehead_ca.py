from locations.storefinders.stockist import StockistSpider


class BridgeheadCASpider(StockistSpider):
    name = "bridgehead_ca"
    item_attributes = {
        "brand_wikidata": "Q4966509",
        "brand": "Bridgehead",
    }
    key = "u15904"
