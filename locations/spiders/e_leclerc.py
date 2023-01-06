from locations.storefinders.woosmap import WoosmapSpider


class ELeclercSpider(WoosmapSpider):
    name = "e_leclerc"
    item_attributes = {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"}
    key = "woos-6256d36f-af9b-3b64-a84f-22b2342121ba"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.e.leclerc"}}

    def parse_item(self, item, feature, **kwargs):
        item["website"] = feature["properties"]["user_properties"].get("urlStore")
        item["extras"] = {
            "store_type": feature["properties"]["user_properties"].get("commercialActivity", {}).get("label")
        }
        yield item
