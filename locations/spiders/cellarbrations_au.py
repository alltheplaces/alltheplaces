from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class CellarbrationsAUSpider(StorefrontgatewaySpider):
    name = "cellarbrations_au"
    item_attributes = {"brand": "Cellarbrations", "brand_wikidata": "Q109807592"}
    allowed_domains = ["storefrontgateway.cellarbrations.com.au"]
    start_urls = [
        "https://storefrontgateway.cellarbrations.com.au/api/near/-33.867778/151.21/20000/20000/stores",
    ]
