from locations.categories import Categories
from locations.storefinders.wakefern import WakefernSpider


class FairwayMarketUSSpider(WakefernSpider):
    name = "fairway_market_us"
    item_attributes = {
        "brand": "Fairway Market",
        "brand_wikidata": "Q5430910",
        "name": "Fairway Market",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.fairwaymarket.com/"]
