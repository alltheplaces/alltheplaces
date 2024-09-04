from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class LundsAndByerlysSpider(StorefrontgatewaySpider):
    name = "lunds_and_byerlys"
    item_attributes = {
        "brand": "Lunds & Byerlys",
        "brand_wikidata": "Q19903424",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = [
        "https://storefrontgateway.lundsandbyerlys.com/api/stores",
    ]