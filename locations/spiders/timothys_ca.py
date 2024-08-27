from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class TimothysCASpider(SuperStoreFinderSpider):
    name = "timothys_ca"
    item_attributes = {
        "brand_wikidata": "Q7807011",
        "brand": "Timothy's",
    }
    allowed_domains = [
        "timothyscafes.com",
    ]
