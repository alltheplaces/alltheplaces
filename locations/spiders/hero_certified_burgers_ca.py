from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HeroCertifiedBurgersCASpider(WPStoreLocatorSpider):
    name = "hero_certified_burgers_ca"
    item_attributes = {
        "brand_wikidata": "Q5742641",
        "brand": "Hero Certified Burgers",
    }
    allowed_domains = [
        "heroburgers.com",
    ]
    time_format = "%I:%M %p"
