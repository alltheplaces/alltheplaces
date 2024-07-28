from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PharmasaveAUSpider(WPStoreLocatorSpider):
    name = "pharmasave_au"
    item_attributes = {"brand": "PharmaSave", "brand_wikidata": "Q63367906"}
    allowed_domains = ["www.pharmasave.com.au"]
    time_format = "%I:%M %p"
