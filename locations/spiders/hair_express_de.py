from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class HairExpressDESpider(KlierHairGroupSpider):
    name = "hair_express_de"
    start_urls = ["https://www.hairexpress-friseur.de/salons/"]
    item_attributes = {"brand": "Hair Express", "brand_wikidata": "Q57550814"}
