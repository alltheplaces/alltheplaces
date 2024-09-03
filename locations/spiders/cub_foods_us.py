from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class CubFoodsUSSpider(StorefrontgatewaySpider):
    name = "cub_foods_us"
    item_attributes = {"brand": "Cub Foods", "brand_wikidata": "Q5191916"}
    start_urls = ["https://storefrontgateway.cub.com/api/stores"]
    requires_proxy = "US"  # Cloudflare geoblocking in use
