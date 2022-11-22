from locations.storefinders.woosmap import WoosmapSpider


class CarrefourFrSpider(WoosmapSpider):
    name = "carrefour_fr"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}

    key = "woos-26fe76aa-ff24-3255-b25b-e1bde7b7a683"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.carrefour.fr"}
    }

    def parse_item(self, item, feature, **kwargs):
        item["extras"] = {
            "store_type": feature.get("properties").get("types"),
        }
        if "CARREFOUR EXPRESS" in item["extras"]["store_type"]:
            item["brand"] = "CARREFOUR EXPRESS"
            item["brand_wikidata"] = "Q2940190"
        yield item
