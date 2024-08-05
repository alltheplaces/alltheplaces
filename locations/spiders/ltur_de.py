from locations.storefinders.uberall import UberallSpider


class LturDESpider(UberallSpider):
    name = "ltur_de"
    item_attributes = {
        "brand_wikidata": "Q519040",
        "brand": "ltur",
    }
    key = "EcxuEjpLBEDd10z2vTkvABBLnX2sXD"
