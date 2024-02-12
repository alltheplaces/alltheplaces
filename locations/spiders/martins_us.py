from locations.storefinders.freshop import FreshopSpider
from locations.categories import Categories


class MartinsUSSpider(FreshopSpider):
    name = "martins_us"
    app_key = "martins"
    item_attributes = {
        "brand": "Martin's Super Markets",
        "brand_wikidata": "Q7573912",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
