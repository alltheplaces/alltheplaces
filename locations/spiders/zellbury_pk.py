from locations.storefinders.storerocket import StoreRocketSpider


class ZellburyPKSpider(StoreRocketSpider):
    name = "zellbury_pk"
    item_attributes = {"brand": "Zellbury", "brand_wikidata": "Q85171530"}
    storerocket_id = "xw8VXEY4aE"
