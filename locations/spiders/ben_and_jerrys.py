from chompjs import parse_js_object

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class BenAndJerrysSpider(Where2GetItSpider):
    download_timeout = 60
    name = "ben_and_jerrys"
    item_attributes = {"brand": "Ben & Jerry's", "brand_wikidata": "Q816412"}
    api_key = "3D71930E-EC80-11E6-A0AE-8347407E493E"
    api_filter = {"icon": {"in": "default,SHOP"}}

    def parse_item(self, item, location):
        try:
            shop_info = parse_js_object(location["jsonshopinfo"])
            try:
                shop = shop_info[0]["ShopInfoContent"][0]["StoreDetails"]
                if url := shop.get("WebsiteURL"):
                    item["website"] = url
            except (TypeError, IndexError):
                pass
        except ValueError:
            pass
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        apply_yes_no(Extras.DELIVERY, item, location["offersdelivery"] == "1")
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if location.get(day.lower()) in [None, ""]:
                continue
            if "closed" in location.get(day.lower()):
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_ranges_from_string(day + " " + location.get(day.lower()))
        # this source is not listing standalone ice cream POIs from this brand
        # but rather known locations where their ice cream is provided
        item.pop("amenity", None)
        item.pop("cuisine", None)
        apply_yes_no("ice_cream", item, "yes")
        yield item
