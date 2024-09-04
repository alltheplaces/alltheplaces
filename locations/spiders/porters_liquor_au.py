from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider

class PortersLiquorAuSpider(StorefrontgatewaySpider):
    name = "porters_liquor_au"
    start_urls = [
        "https://storefrontgateway.portersliquor.com.au/api/stores",
    ]
    item_attributes = {
        "brand": "Porters Liquor",
        "extras": Categories.SHOP_ALCOHOL.value
    }

