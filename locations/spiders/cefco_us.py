from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.storefinders.storepoint import StorepointSpider


class CefcoUSSpider(StorepointSpider):
    name = "cefco_us"
    item_attributes = {"brand": "CEFCO", "brand_wikidata": "Q110209230"}
    key = "164a579f9b686a"

    def parse_item(self, item, location):
        item["ref"] = item["name"].split("#", 1)[1].strip()
        item.pop("name", None)
        item.pop("website", None)
        apply_category(Categories.SHOP_CONVENIENCE, item)
        if "GAS" in location["tags"].upper() or "DIESEL" in location["tags"].upper():
            apply_category(Categories.FUEL_STATION, item)
        if "BEER" in location["tags"].upper():
            apply_category(Categories.SHOP_ALCOHOL, item)
        if "FOOD" in location["tags"].upper():
            apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Fuel.DIESEL, item, "DIESEL" in location["tags"].upper(), False)
        apply_yes_no(Extras.CAR_WASH, item, "CAR WASH" in location["tags"].upper(), False)
        yield item
