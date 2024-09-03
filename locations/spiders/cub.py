from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class CubSpider(StorefrontgatewaySpider):
    name = "cub"
    item_attributes = {"brand": "Cub Foods", "brand_wikidata": "Q5191916"}
    start_urls = ["https://storefrontgateway.cub.com/api/stores"]
    requires_proxy = "US"  # Cloudflare geoblocking in use
