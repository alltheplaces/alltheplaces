from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class MagasinVertFRSpider(AmastyStoreLocatorSpider):
    name = "magasin_vert_fr"
    allowed_domains = [
        "www.monmagasinvert.fr",
    ]
    item_attributes = {"brand": "Magasin Vert", "brand_wikidata": "Q16661975"}
