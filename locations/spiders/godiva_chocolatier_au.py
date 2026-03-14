from locations.storefinders.stockist import StockistSpider


class GodivaChocolatierAUSpider(StockistSpider):
    name = "godiva_chocolatier_au"
    item_attributes = {"brand": "Godiva", "brand_wikidata": "Q931084"}
    key = "u17509"
