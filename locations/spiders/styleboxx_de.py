from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class StyleboxxDESpider(KlierHairGroupSpider):
    name = "styleboxx_de"
    start_urls = ["https://www.styleboxx-klier.de/salons/"]
    item_attributes = {"brand": "Styleboxx", "brand_wikidata": "Q121888237"}
