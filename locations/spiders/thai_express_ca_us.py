from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class ThaiExpressCAUSSpider(SuperStoreFinderSpider):
    name = "thai_express_ca_us"
    item_attributes = {
        "brand_wikidata": "Q7711610",
        "brand": "Thaï Express",
    }
    allowed_domains = [
        "locations.thaiexpress.ca",
    ]
