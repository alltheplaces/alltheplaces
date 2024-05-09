from locations.categories import Categories
from locations.storefinders.uberall import UberallSpider


class ArdeneSpider(UberallSpider):
    name = "ardene"
    item_attributes = {"brand": "Ardene", "brand_wikidata": "Q2860764", "extras": Categories.SHOP_CLOTHES.value}
    key = "APLOifTJjDLpXnd0K1bTlQmbKKM3mt"
