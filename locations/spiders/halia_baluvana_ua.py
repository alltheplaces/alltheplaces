from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HaliaBaluvanaUASpider(AgileStoreLocatorSpider):
    name = "halia_baluvana_ua"
    item_attributes = {
        "brand_wikidata": "Q117744813",
        "brand": "Галя Балувана",
    }
    allowed_domains = [
        "haliabaluvana.com",
    ]
