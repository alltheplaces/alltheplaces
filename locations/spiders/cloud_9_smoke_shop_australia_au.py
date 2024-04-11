from locations.storefinders.stockist import StockistSpider


class Cloud9SmokeShopAustraliaAUSpider(StockistSpider):
    name = "cloud_9_smoke_shop_australia_au"
    item_attributes = {"brand": "Cloud 9 Smoke Shop Australia", "brand_wikidata": "Q117822054"}
    key = "u19322"

    def parse_item(self, item, location):
        yield item
