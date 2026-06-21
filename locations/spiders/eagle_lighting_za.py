from locations.categories import Categories, apply_category
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class EagleLightingZASpider(AgileStoreLocatorSpider):
    name = "eagle_lighting_za"
    item_attributes = {"brand": "Eagle Lighting", "brand_wikidata": "Q140303240"}
    allowed_domains = ["eaglelighting.co.za"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "")
        item.pop("website", "")
        apply_category(Categories.SHOP_LIGHTING, item)
        yield item
