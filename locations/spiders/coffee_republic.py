from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class CoffeeRepublicSpider(SuperStoreFinderSpider):
    name = "coffee_republic"
    item_attributes = {
        "brand_wikidata": "Q5140923",
        "brand": "Coffee Republic",
    }
    allowed_domains = [
        "coffeerepublic.co.uk",
    ]
