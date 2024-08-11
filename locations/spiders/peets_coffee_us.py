from locations.categories import Categories, Extras, PaymentMethods, apply_yes_no
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class PeetsCoffeeUSSpider(StockistSpider):
    name = "peets_coffee_us"
    item_attributes = {"brand": "Peet's Coffee", "brand_wikidata": "Q1094101", "extras": Categories.COFFEE_SHOP.value}
    key = "u5687"

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        for field in location["custom_fields"]:
            if field["name"].startswith("Hours:"):
                day = field["name"][6:]
                hours = field["value"]
                if hours.endswith("pm") and "-" in hours and ":" in hours:
                    open, close = hours.split("-")
                    closeHour, closeMinute = close.split(":")
                    closeHour = int(closeHour)
                    if closeHour >= 12:
                        closeHour -= 12
                        close = str(closeHour) + ":" + closeMinute
                    hours = open + "-" + close
                item["opening_hours"].add_ranges_from_string(day + " " + hours)

            if field["name"] == "Order Online" and item.get("website") is None:
                item["website"] = field["value"]
            if field["name"] == "Type" and field["value"] == "Licensed Partner":
                item["located_in"] = item.pop("name")

        item["branch"] = item.pop("name", None)

        for feature in location["filters"]:
            apply_yes_no(PaymentMethods.CONTACTLESS, item, feature["name"] == "Contactless Payments")
            apply_yes_no("payment:gift_card", item, feature["name"] == "Accepts Peet's Cards")
            apply_yes_no(Extras.BREAKFAST, item, feature["name"] == "Warm Breakfast")
            apply_yes_no(Extras.WIFI, item, feature["name"] == "Free Wi-Fi")
            apply_yes_no(Extras.DELIVERY, item, feature["name"] == "Delivery")

        yield item
