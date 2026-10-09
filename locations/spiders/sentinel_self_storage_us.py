from locations.storefinders.storage_pug import StoragePugSpider


class SentinelSelfStorageUSSpider(StoragePugSpider):
    name = "sentinel_self_storage_us"
    item_attributes = {"brand": "Sentinel Self Storage"}
    start_urls = ["https://www.storeatsentinel.com/view-locations"]
