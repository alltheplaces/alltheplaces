from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FreshslicePizzaCASpider(WPStoreLocatorSpider):
    name = "freshslice_pizza_ca"
    item_attributes = {
        "brand_wikidata": "Q5503082",
        "brand": "Freshslice Pizza",
    }
    allowed_domains = [
        "www.freshslice.com",
    ]
    time_format = "%I:%M %p"
