from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class EuromobilNLSpider(WPStoreLocatorSpider):
    name = "euromobil_nl"
    item_attributes = {"brand": "Euromobil", "brand_wikidata": "Q1375118"}
    allowed_domains = ["euromobil.nl"]
