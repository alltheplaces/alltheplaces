from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LordOfTheFriesAUNZSpider(WPStoreLocatorSpider):
    name = "lord_of_the_fries_au_nz"
    item_attributes = {
        "brand_wikidata": "Q104088629",
        "brand": "Lord of the Fries",
    }
    allowed_domains = [
        "www.lordofthefries.com.au",
    ]
