from locations.storefinders.storerocket import StoreRocketSpider


class EarlySettlerSpider(StoreRocketSpider):
    name = "early_settler"
    item_attributes = {"brand": "Early Settler", "brand_wikidata": "Q111080173"}
    storerocket_id = "Ax869awJy1"
