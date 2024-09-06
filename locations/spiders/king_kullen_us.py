from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class KingKullenUSSpider(StorefrontgatewaySpider):
    name = "king_kullen_us"
    item_attributes = {"brand": "King Kullen", "brand_wikidata": "Q6411832"}
    start_urls = ["https://storefrontgateway.kingkullen.com/api/stores"]
    requires_proxy = "US"  # Cloudflare geoblocking in use
