from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CarpetCourtNZSpider(WPStoreLocatorSpider):
    name = "carpet_court_nz"
    item_attributes = {"brand": "Carpet Court", "brand_wikidata": "Q117156437"}
    allowed_domains = ["carpetcourt.nz"]
    time_format = "%I:%M %p"
