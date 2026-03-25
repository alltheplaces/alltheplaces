from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class ChurchFootwearSpider(JSONBlobSpider):
    name = "church_footwear"
    item_attributes = {"brand": "Church's", "brand_wikidata": "Q2967663"}
    start_urls = ["https://api.church-footwear.com/anon/mwstorestore/store/v2?langId=en_GB"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "api.church-footwear.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.church-footwear.com/",
            "storeId": "churchsStore-GB",
            "Origin": "https://www.church-footwear.com",
        },
    }
    locations_key = "allStores"
