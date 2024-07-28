from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class OlliesPlaceAUSpider(StockistSpider):
    name = "ollies_place_au"
    item_attributes = {
        "brand": "Ollies Place",
        "brand_wikidata": "Q126165914",
        "extras": Categories.SHOP_BABY_GOODS.value,
    }
    key = "u20939"
