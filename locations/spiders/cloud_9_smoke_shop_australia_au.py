import json

from locations.storefinders.metizsoft import MetizsoftSpider


class Cloud9SmokeShopAustraliaAUSpider(MetizsoftSpider):
    name = "cloud_9_smoke_shop_australia_au"
    item_attributes = {"brand": "Cloud 9 Smoke Shop Australia", "brand_wikidata": "Q117822054"}
    shopify_url = "cloud-9-smoke-shop-australia.myshopify.com"

    def parse_item(self, item, location):
        extra_fields = json.loads(location["extra_fields"])
        for extra_field in extra_fields:
            if extra_field["fieldnm"] == "764@Mobile":
                item["phone"] = extra_field["fieldvalue"].strip()
                break
        item.pop("website")
        yield item
