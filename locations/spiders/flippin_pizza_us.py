from locations.json_blob_spider import JSONBlobSpider


# A variant on the SuperStoreFinder plugin
class FlippinPizzaUSSpider(JSONBlobSpider):
    name = "flippin_pizza_us"
    locations_key = "item"
    item_attributes = {
        "brand_wikidata": "Q113138241",
        "brand": "Flippin' Pizza",
    }
    allowed_domains = [
        "flippinpizza.com",
    ]
    start_urls = ["https://flippinpizza.com/wp-content/uploads/ssf-wp-uploads/ssf-data.json"]
