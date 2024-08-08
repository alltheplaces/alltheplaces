from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class GiantMYSpider(SuperStoreFinderSpider):
    name = "giant_my"
    item_attributes = {
        "brand_wikidata": "Q4217013",
        "brand": "Giant Hypermarket",
    }
    allowed_domains = [
        "www.giant.com.my",
    ]
