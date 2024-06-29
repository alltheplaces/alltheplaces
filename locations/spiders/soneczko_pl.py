from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SoneczkoPLSpider(WPStoreLocatorSpider):
    name = "soneczko_pl"
    item_attributes = {
        "brand_wikidata": "Q113230439",
        "brand": "Słoneczko",
    }
    allowed_domains = [
        "sloneczko.zgora.pl",
    ]
