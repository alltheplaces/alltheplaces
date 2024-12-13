from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class MilkyLaneZASpider(YextSearchSpider):
    name = "milky_lane_za"
    item_attributes = {"brand": "Milky Lane", "brand_wikidata": "Q128223693"}
    host = "https://location.milkylane.co.za"

    def parse_item(self, location, item):
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery"), False)

        if item["website"] is None or item["website"] in ["https://www.milkylane.co.za"]:
            item["website"] = location["profile"].get("c_pagesURL")

        if item["extras"].get("website:orders") in ["https://app.milkylane.co.za/", "https://www.milkylane.co.za"]:
            item["extras"].pop("website:orders")

        if item["email"] in ["info@milkylane.co.za"]:
            item.pop("email")

        try:
            if " " in item["street_address"]:
                int(item["street_address"].split(" ", 1)[0])
                item["housenumber"] = item["street_address"].split(" ", 1)[0]
                item["street"] = item["street_address"].split(" ", 1)[1]
        except ValueError:
            pass

        yield item
