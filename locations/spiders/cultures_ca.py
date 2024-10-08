from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class CulturesCASpider(SuperStoreFinderSpider):
    name = "cultures_ca"
    item_attributes = {
        "brand_wikidata": "Q64876898",
        "brand": "Cultures",
    }
    allowed_domains = [
        "cultures-restaurants.com",
    ]
