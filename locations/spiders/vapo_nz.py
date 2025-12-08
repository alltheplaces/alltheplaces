from locations.storefinders.storerocket import StoreRocketSpider


class VapoNZSpider(StoreRocketSpider):
    name = "vapo_nz"
    item_attributes = {"brand": "VAPO", "brand_wikidata": "Q117236856"}
    storerocket_id = "BkJ1KGZpqR"
