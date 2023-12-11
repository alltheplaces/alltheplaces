from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BreWingzSpider(WPStoreLocatorSpider):
    name = "bre_wingz"
    item_attributes = {"brand": "BreWingz", "brand_wikidata": "Q123022531"}
    allowed_domains = ["www.brewingz.com"]
    time_format = "%I:%M %p"
