from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class AmigoUSSpider(AgileStoreLocatorSpider):
    name = "amigo_us"
    item_attributes = {
        "brand_wikidata": "Q4746234",
        "brand": "Amigo",
    }
    allowed_domains = [
        "amigo.com",
    ]
