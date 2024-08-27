from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlohaPokeCoSpider(WPStoreLocatorSpider):
    name = "aloha_poke_co"
    item_attributes = {
        "brand_wikidata": "Q111231031",
        "brand": "Aloha Pokē Co",
    }
    allowed_domains = [
        "www.alohapokeco.com",
    ]
    time_format = "%I:%M %p"
