from locations.categories import Categories
from locations.spiders.medirite_za import MediriteZASpider


class LiquorshopCheckersZASpider(MediriteZASpider):
    name = "liquorshop_checkers_za"
    item_attributes = {
        "brand": "LiquorShop Checkers",
        "brand_wikidata": "Q5089126",
        "extras": Categories.SHOP_ALCOHOL.value,
    }
    brands = ["Checkers LiquorShop"]
