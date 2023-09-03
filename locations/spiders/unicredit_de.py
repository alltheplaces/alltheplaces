from locations.storefinders.uberall import UberallSpider


class UnicreditDeSpider(UberallSpider):
    name = "unicredit_de"
    item_attributes = {"brand": "UniCredit", "brand_wikidata": "Q45568"}
    key = "QZ7auxGUWKL0MfAnUOgweafKIwrXPb"
