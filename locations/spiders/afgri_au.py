from locations.storefinders.storepoint import StorepointSpider


class AfgriAUSpider(StorepointSpider):
    name = "afgri_au"
    item_attributes = {"brand": "AFGRI Equipment", "brand_wikidata": "Q119264464"}
    key = "15f4466ee99d2b"
