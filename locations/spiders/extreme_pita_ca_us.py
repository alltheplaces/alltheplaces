from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class ExtremePitaCAUSSpider(SuperStoreFinderSpider):
    name = "extreme_pita_ca_us"
    item_attributes = {
        "brand_wikidata": "Q5422367",
        "brand": "Extreme Pita",
    }
    allowed_domains = [
        "extremepita.com",
    ]
