from locations.json_blob_spider import JSONBlobSpider


class TheLashLoungeUSSpider(JSONBlobSpider):
    name = "the_lash_lounge_us"
    item_attributes = {"brand": "The Lash Lounge", "brand_wikidata": "Q112765439"}
    start_urls = [
        "https://www.thelashlounge.com/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=fde8aa6ae8&load_all=1&layout=1"
    ]
