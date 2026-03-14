from locations.storefinders.storerocket import StoreRocketSpider


class MooyahSpider(StoreRocketSpider):
    name = "mooyah"
    item_attributes = {"brand": "Mooyah", "brand_wikidata": "Q6908759"}
    storerocket_id = "2BkJ1KzpqR"
