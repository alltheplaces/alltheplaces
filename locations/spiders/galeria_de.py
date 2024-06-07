from locations.storefinders.uberall import UberallSpider


class GaleriaDESpider(UberallSpider):
    name = "galeria_de"
    item_attributes = {"brand": "Galeria", "brand_wikidata": "Q80220059"}
    key = "yQ7AVSxcAEpMdcx1mMWkSEwH8SenmY"
