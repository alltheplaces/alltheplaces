from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class AmericanEagleOutfittersSpider(YextSpider):
    name = "american_eagle_outfitters"
    AMERICAN_EAGLE = {"brand": "American Eagle Outfitters", "brand_wikidata": "Q2842931"}
    AERIE = {"brand": "Aerie", "brand_wikidata": "Q25351619"}
    api_key = "90d8e45747b6a14476d8f1a327f692fe"
    drop_attributes = {"image", "twitter"}

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["website"] = urljoin("https://storelocations.ae.com/", location.get("slug", ""))
        if "OFFLINE" in item["name"]:
            item["name"] = "OFFLINE By Aerie"
            item.update(self.AERIE)
        elif item["name"].startswith("Aerie"):
            item.update(self.AERIE)
        elif item["name"].startswith("Todd Snyder"):
            item["brand"] = "Todd Snyder"
        elif "American Eagle" in item["name"]:
            item["name"] = None
            item.update(self.AMERICAN_EAGLE)
        else:  # Unsubscribed + AEO Distribution Center + Test stores
            return
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
