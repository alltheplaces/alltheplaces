from locations.storefinders.uberall import UberallSpider


class PenningtonsCASpider(UberallSpider):
    name = "penningtons_ca"
    item_attributes = {
        "brand_wikidata": "Q16956527",
        "brand": "Penningtons",
    }
    key = "plEhL7SEWWjub5NBhsr8Iidzl8GgaX"
