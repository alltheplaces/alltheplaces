from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class AmericanEagleOutfittersSpider(YextSpider):
    name = "american_eagle_outfitters"
    item_attributes = {"brand": "American Eagle Outfitters", "brand_wikidata": "Q2842931"}
    AERIE = {"brand": "Aerie", "brand_wikidata": "Q25351619"}
    OFFLINE = {"brand": "OFFLINE By Aerie", "brand_wikidata": ""}
    api_key = "90d8e45747b6a14476d8f1a327f692fe"
    drop_attributes = {"image", "twitter"}

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if item["name"].title().startswith("Aerie"):
            item.update(self.AERIE)
        elif item["name"].title().startswith("Offline"):
            item.update(self.OFFLINE)
            apply_category(Categories.SHOP_CLOTHES, item)
        yield item
