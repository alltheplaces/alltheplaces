from locations.storefinders.storage_pug import StoragePugSpider


class GlobalSelfStorageUSSpider(StoragePugSpider):
    name = "global_self_storage_us"
    item_attributes = {"brand": "Global Self Storage"}
    start_urls = ["https://www.globalselfstorage.us/view-locations"]
