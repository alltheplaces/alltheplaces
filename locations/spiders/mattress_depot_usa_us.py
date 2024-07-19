from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MattressDepotUsaUSSpider(WPStoreLocatorSpider):
    name = "mattress_depot_usa_us"
    item_attributes = {"brand": "Mattress Depot USA", "brand_wikidata": "Q108413386"}
    drop_attributes = {"addr_full"}
    allowed_domains = ["www.mattressdepotusa.com"]
    time_format = "%I:%M %p"
