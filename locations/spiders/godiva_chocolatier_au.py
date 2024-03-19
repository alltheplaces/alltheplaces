from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class GodivaChocolatierAUSpider(StockistSpider):
    name = "godiva_chocolatier_au"
    item_attributes = {
        "brand": "Godiva Chocolatier",
        "brand_wikidata": "Q931084",
        "extras": Categories.SHOP_CHOCOLATE.value,
    }
    key = "u17509"
