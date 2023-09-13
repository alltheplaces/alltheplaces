from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DoorsPlusAUSpider(WPStoreLocatorSpider):
    name = "doors_plus_au"
    item_attributes = {"brand": "Doors Plus", "brand_wikidata": "Q78945358"}
    allowed_domains = ["www.doorsplus.com.au"]
    time_format = "%I:%M %p"
