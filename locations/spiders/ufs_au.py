from locations.storefinders.storeify import StoreifySpider


class UfsAUSpider(StoreifySpider):
    name = "ufs_au"
    item_attributes = {"brand": "UFS", "brand_wikidata": "Q63367573"}
    api_key = "ufs-pharmacies.myshopify.com"
