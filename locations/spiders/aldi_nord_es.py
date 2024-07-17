from locations.categories import Categories
from locations.storefinders.uberall import UberallSpider


class AldiNordESSpider(UberallSpider):
    name = "aldi_nord_es"
    item_attributes = {"brand_wikidata": "Q41171373", "extras": Categories.SHOP_SUPERMARKET.value}
    drop_attributes = {"name"}
    key = "ALDINORDES_kRpYT2HM1bFjL9vTpn5q0JupSiXqnB"
