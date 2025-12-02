from locations.json_blob_spider import JSONBlobSpider


class FamilymartMYSpider(JSONBlobSpider):
    name = "familymart_my"
    item_attributes = {"brand": "FamilyMart", "brand_wikidata": "Q11247682"}
    start_urls = ["https://familymart.com.my/stores.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 50}
    no_refs = True
