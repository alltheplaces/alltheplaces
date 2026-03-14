from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class SpringMarketUSSpider(StorefrontgatewaySpider):
    name = "spring_market_us"
    item_attributes = {
        "brand": "Spring Market",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://storefrontgateway.spring-market.com/api/stores"]
