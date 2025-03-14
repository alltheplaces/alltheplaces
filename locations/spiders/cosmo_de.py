from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class CosmoDESpider(KlierHairGroupSpider):
    name = "cosmo_de"
    start_urls = ["https://www.cosmo-hairshop.de/shops/"]
    item_attributes = {"brand": "Cosmo", "brand_wikidata": "Q121888284"}
