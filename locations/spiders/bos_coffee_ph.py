from locations.storefinders.metizsoft import MetizsoftSpider


class BosCoffeePHSpider(MetizsoftSpider):
    name = "bos_coffee_ph"
    item_attributes = {
        "brand_wikidata": "Q30591352",
        "brand": "Bo's Coffee",
    }
    shopify_url = "bos-coffee.myshopify.com"
