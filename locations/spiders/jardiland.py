from locations.storefinders.woosmap import WoosmapSpider


class JardilandSpider(WoosmapSpider):
    name = "jardiland"
    item_attributes = {"brand": "Jardiland", "brand_wikidata": "Q3162276"}
    key = "jardiland-woos-staging"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.jardiland.com/"}}

    def parse_item(self, item, feature, **kwargs):
        item["website"] = feature["properties"]["user_properties"].get("urlStore")
        item["extras"] = {
            "store_type": feature["properties"]["user_properties"].get("commercialActivity", {}).get("label")
        }
        yield item
