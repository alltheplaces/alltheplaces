from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class JazenTeaCAUSSpider(WPStoreLocatorSpider):
    name = "jazen_tea_ca_us"
    item_attributes = {
        "brand_wikidata": "Q114989479",
        "brand": "Jazen Tea",
    }
    allowed_domains = [
        "www.jazentea.com",
    ]
    time_format = "%H:%M %p"
