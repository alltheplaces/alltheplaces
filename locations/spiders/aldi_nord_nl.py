from locations.categories import Categories
from locations.storefinders.uberall import UberallSpider


class AldiNordNLSpider(UberallSpider):
    name = "aldi_nord_nl"
    item_attributes = {"brand_wikidata": "Q41171373", "extras": Categories.SHOP_SUPERMARKET.value}
    drop_attributes = {"name"}
    key = "ALDINORDNL_8oqeY3lnn9MTZdVzFn4o0WCDVTauoZ"
