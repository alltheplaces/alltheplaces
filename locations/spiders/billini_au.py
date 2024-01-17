from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class BilliniAUSpider(StockistSpider):
    name = "billini_au"
    item_attributes = {"brand": "Billini", "brand_wikidata": "Q117747826", "extras": Categories.SHOP_CLOTHES.value}
    key = "u5133"
