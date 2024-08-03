from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class KidstuffAUSpider(StockistSpider):
    name = "kidstuff_au"
    item_attributes = {"brand": "Kidstuff", "brand_wikidata": "Q117746407", "extras": Categories.SHOP_TOYS.value}
    key = "u8053"
