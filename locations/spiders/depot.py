from locations.storefinders.uberall import UberallSpider


class DepotSpider(UberallSpider):
    name = "depot"
    item_attributes = {"brand": "Depot", "brand_wikidata": "Q1191740"}
    key = "m1b7cz6vaOkcFCCNqLfkO8QgM2pjhA"
