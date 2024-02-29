from locations.hours import DAYS_NL
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HiziHairNLSpider(WPStoreLocatorSpider):
    name = "hizi_hair_nl"
    days = DAYS_NL  # Not supplied, but if they ever are
    item_attributes = {
        "brand_wikidata": "Q122903761",
        "brand": "Hizi Hair",
    }
    allowed_domains = [
        "www.hizihair.nl",
    ]
