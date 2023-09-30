from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class TacoTimeCASpider(SuperStoreFinderSpider):
    name = "taco_time_ca"
    item_attributes = {"brand": "Taco Time", "brand_wikidata": "Q7673969"}
    allowed_domains = ["tacotimecanada.com"]
