from locations.storefinders.stockist import StockistSpider


class BuyBuyBabySpider(StockistSpider):
    name = "buy_buy_baby"
    item_attributes = {"brand": "Buy Buy Baby", "brand_wikidata": "Q5003352"}
    key = "u21140"
