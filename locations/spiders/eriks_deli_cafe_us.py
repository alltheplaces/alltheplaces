from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class EriksDeliCafeUSSpider(WPStoreLocatorSpider):
    name = "eriks_deli_cafe_us"
    item_attributes = {
        "brand_wikidata": "Q116922917",
        "brand": "Erik's DeliCafé",
    }
    allowed_domains = [
        "eriksdelicafe.com",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    time_format = "%I:%M %p"
