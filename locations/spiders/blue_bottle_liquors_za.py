from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BlueBottleLiquorsZASpider(AgileStoreLocatorSpider):
    name = "blue_bottle_liquors_za"
    item_attributes = {
        "brand": "Blue Bottle Liquors",
        "brand_wikidata": "Q116861688",
        "extras": Categories.SHOP_ALCOHOL.value,
    }

    allowed_domains = [
        "bluebottleliquors.co.za",
    ]
