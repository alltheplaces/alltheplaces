from locations.categories import Categories
from locations.storefinders.where2getit import Where2GetItSpider


class FjallravenSpider(Where2GetItSpider):
    name = "fjallraven"
    item_attributes = {
        "brand": "Fjällräven",
        "brand_wikidata": "Q1422481",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    api_brand_name = "fjallraven"
    api_key = "FE424754-8D89-11E7-A07A-F839407E493E"
    api_filter = {
        "brand_store": {"eq": "1"},
    }
