from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SoulPattinsonChemistAUSpider(WPStoreLocatorSpider):
    name = "soul_pattinson_chemist_au"
    item_attributes = {"brand": "Soul Pattinson Chemist", "brand_wikidata": "Q117225301"}
    allowed_domains = ["soulpattinson.com.au"]
    time_format = "%I:%M %p"
