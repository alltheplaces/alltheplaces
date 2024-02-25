from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PetlandUSSpider(WPStoreLocatorSpider):
    name = "petland_us"
    item_attributes = {
        "brand_wikidata": "Q17111474",
        "brand": "Petland",
    }
    allowed_domains = [
        "petland.com",
    ]
    time_format = "%I:%M %p"
