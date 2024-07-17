from locations.categories import Categories
from locations.storefinders.freshop import FreshopSpider


class SentryFoodsSpider(FreshopSpider):
    name = "sentry_foods"
    item_attributes = {
        "brand": "Sentry Foods",
        "brand_wikidata": "Q7451397",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    app_key = "sentry_stores"
