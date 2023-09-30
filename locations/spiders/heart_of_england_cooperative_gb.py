from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class HeartOfEnglandCooperativeGBSpiderSpider(SuperStoreFinderSpider):
    name = "heart_of_england_cooperative_gb"
    item_attributes = {"brand": "Heart of England Co-operative", "brand_wikidata": "Q5692254"}
    start_urls = ["https://www.cawtest.com/heartofengland/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]
