from locations.categories import Categories
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class MtnDealsZASpider(SuperStoreFinderSpider):
    name = "mtn_deals_za"
    item_attributes = {
        "brand_wikidata": "Q1813361",
        "brand": "MTN",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    allowed_domains = [
        "mtndeals.co.za",
    ]
