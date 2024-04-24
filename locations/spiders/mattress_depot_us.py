from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MattressDepotUSAUSSpider(WPStoreLocatorSpider):
    name = "mattress_depot_usa_us"
    item_attributes = {
        "brand_wikidata": "Q108413386",
        "brand": "Mattress Depot USA",
    }
    allowed_domains = [
        "www.mattressdepotusa.com",
    ]
    time_format = "%H:%M %p"
