from locations.storefinders.storepoint import StorepointSpider


class AmericanDeliUSSpider(StorepointSpider):
    name = "american_deli_us"
    item_attributes = {
        "brand_wikidata": "Q119993570",
        "brand": "American Deli",
    }
    key = "164e39b0a67730"
