from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class BrookshiresUSSpider(StorefrontgatewaySpider):
    name = "brookshires_us"
    item_attributes = {"brand": "Brookshire's", "brand_wikidata": "Q4975085"}
    start_urls = ["https://storefrontgateway.brookshires.com/api/stores"]
    requires_proxy = "US"  # Cloudflare geoblocking
