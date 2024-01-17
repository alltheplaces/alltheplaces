from locations.storefinders.uberall import UberallSpider


class KarstadtDESpider(UberallSpider):
    name = "karstadt_de"
    item_attributes = {"brand": "Karstadt", "brand_wikidata": "Q182910"}
    key = "yQ7AVSxcAEpMdcx1mMWkSEwH8SenmY"
