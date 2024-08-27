from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class SaveOnFoodsCASpider(StorefrontgatewaySpider):
    name = "save_on_foods_ca"
    item_attributes = {"brand": "Save-On-Foods", "brand_wikidata": "Q7427974"}
    start_urls = ["https://storefrontgateway.saveonfoods.com/api/stores"]
