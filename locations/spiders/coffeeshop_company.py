from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class CoffeeshopCompanySpider(SuperStoreFinderSpider):
    name = "coffeeshop_company"
    item_attributes = {
        "brand_wikidata": "Q873767",
        "brand": "Coffeeshop Company",
    }
    allowed_domains = [
        "www.coffeeshopcompany.com",
    ]
