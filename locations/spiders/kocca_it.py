from locations.storefinders.storepoint import StorepointSpider


class KoccaITSpider(StorepointSpider):
    name = "kocca_it"
    key = "162eb92660e22f"
    item_attributes = {"brand": "Kocca", "brand_wikidata": "Q122167421"}
