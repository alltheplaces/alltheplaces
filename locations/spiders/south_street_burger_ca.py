from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class SouthStreetBurgerCASpider(SuperStoreFinderSpider):
    name = "south_street_burger_ca"
    item_attributes = {
        "brand_wikidata": "Q123410175",
        "brand": "South Street Burger",
    }
    allowed_domains = [
        "southstreetburger.com",
    ]
