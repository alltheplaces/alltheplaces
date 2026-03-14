from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class KlierDESpider(KlierHairGroupSpider):
    name = "klier_de"
    start_urls = ["https://www.klier.de/salons/"]
    item_attributes = {"brand": "Klier", "brand_wikidata": "Q121888036"}
