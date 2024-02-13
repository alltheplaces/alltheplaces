from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DaViNailsCAUSSpider(WPStoreLocatorSpider):
    name = "davi_nails_ca_us"
    item_attributes = {
        "brand_wikidata": "Q108726836",
        "brand": "DaVi Nails",
        "extras": Categories.SHOP_BEAUTY.value,
    }
    allowed_domains = [
        "davinails.com",
    ]
