from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class BrookshiresUSSpider(StorefrontgatewaySpider):
    name = "brookshires_us"
    item_attributes = {"brand": "Brookshires", "brand_wikidata": "Q7427974"}
    start_urls = ["https://storefrontgateway.brookshires.com/api/stores"]
