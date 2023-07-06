from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LundsAndByerlysSpider(WPStoreLocatorSpider):
    name = "lundsandbyerlys"
    item_attributes = {"brand": "Lunds & Byerlys", "brand_wikidata": "Q19903424"}
    allowed_domains = ["lundsandbyerlys.com"]
