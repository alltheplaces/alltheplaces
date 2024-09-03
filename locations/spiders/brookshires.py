from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class BrookshiresSpider(StorefrontgatewaySpider):
    name = "brookshires"
    item_attributes = {"brand": "Save-On-Foods", "brand_wikidata": "Q7427974"}
    start_urls = ["https://storefrontgateway.brookshires.com/api/stores"]
