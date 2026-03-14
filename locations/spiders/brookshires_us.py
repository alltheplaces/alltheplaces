from locations.categories import Categories, apply_category
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class BrookshiresUSSpider(StorefrontgatewaySpider):
    name = "brookshires_us"
    item_attributes = {"brand": "Brookshire's", "brand_wikidata": "Q4975085"}
    start_urls = ["https://storefrontgateway.brookshires.com/api/stores"]
    requires_proxy = "US"  # Cloudflare geoblocking

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
