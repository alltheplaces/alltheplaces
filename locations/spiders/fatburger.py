from locations.storefinders.uberall import UberallSpider


class FatburgerSpider(UberallSpider):
    name = "fatburger"
    item_attributes = {"brand": "Fatburger", "brand_wikidata": "Q1397976"}
    key = "BBOAPSVZOXCPKFUV"
