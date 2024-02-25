from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ShopMetroPHSpider(AgileStoreLocatorSpider):
    name = "shop_metro_ph"
    allowed_domains = [
        "shopmetro.ph",
    ]
    item_attributes = {
        "brand_wikidata": "Q23808789",
        "brand": "ShopMetro",
    }
