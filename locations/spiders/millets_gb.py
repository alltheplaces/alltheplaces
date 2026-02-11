from locations.json_blob_spider import JSONBlobSpider

class MilletsGBSpider(JSONBlobSpider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = ["https://integrations-c3f9339ff060a907cbd8.o2.myshopify.dev/api/stores?fascia=Millets&limit=48&radius=100&fields=address%2Cname%2CmainPhone%2Cservices%2Chours%2Cc_fullName%2Cc_storeType%2CphotoGallery"]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}
