from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BaskinRobbinsGBIESpider(AgileStoreLocatorSpider):
    name = "baskin_robbins_gb_ie"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    allowed_domains = ["baskinrobbins.co.uk"]
