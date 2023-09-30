from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class PatelBrothersUSSpider(SuperStoreFinderSpider):
    name = "patel_brothers_us"
    item_attributes = {"brand": "Patel Brothers", "brand_wikidata": "Q55641396"}
    allowed_domains = ["www.patelbros.com"]
