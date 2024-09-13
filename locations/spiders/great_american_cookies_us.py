from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GreatAmericanCookiesUSSpider(WPStoreLocatorSpider):
    name = "great_american_cookies_us"
    item_attributes = {
        "brand_wikidata": "Q5598629",
        "brand": "Great American Cookies",
    }
    allowed_domains = [
        "www.greatamericancookies.com",
    ]
    time_format = "%I:%M %p"
