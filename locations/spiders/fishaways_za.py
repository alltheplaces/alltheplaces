from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class FishawaysZASpider(YextSearchSpider):
    name = "fishaways_za"
    item_attributes = {"brand": "Fishaways", "brand_wikidata": "Q116618989"}
    host = "https://location.fishaways.co.za"

    def parse_item(self, location, item):
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery"))
        item["extras"]["website:menu"] = location["profile"].get("menuUrl")
        yield item
