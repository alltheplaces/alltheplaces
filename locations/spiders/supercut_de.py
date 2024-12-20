from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class SupercutDESpider(KlierHairGroupSpider):
    name = "supercut_de"
    start_urls = ["https://www.supercut.de/salonfinder/"]
    item_attributes = {"brand": "Super Cut", "brand_wikidata": "Q64139077"}
