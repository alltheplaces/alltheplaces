from locations.storefinders.storeify import StoreifySpider


class NewspowerAUSpider(StoreifySpider):
    name = "newspower_au"
    item_attributes = {"brand": "Newspower", "brand_wikidata": "Q120670137"}
    api_key = "newspower-australia.myshopify.com"
    domain = "https://newspower.com.au/"
