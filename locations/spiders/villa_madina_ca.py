from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class VillaMadinaCASpider(SuperStoreFinderSpider):
    name = "villa_madina_ca"
    item_attributes = {"brand": "Villa Madina", "brand_wikidata": "Q64876884"}
    allowed_domains = ["villamadina.com"]
