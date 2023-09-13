from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class UltraTuneAUSpider(AgileStoreLocatorSpider):
    name = "ultra_tune_au"
    item_attributes = {"brand": "Ultra Tune", "brand_wikidata": "Q29025649"}
    allowed_domains = ["www.ultratune.com.au"]
