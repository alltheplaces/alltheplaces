from locations.storefinders.uberall import UberallSpider


class NettoFRSpider(UberallSpider):
    name = "netto_fr"
    item_attributes = {"brand": "Netto", "brand_wikidata": "Q2720988"}
    key = "OWc3zgl9ql555j9wvYm0ecrD94vaeK"
