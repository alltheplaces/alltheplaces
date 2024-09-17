from urllib.parse import parse_qs, urlparse

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
                    # Find and fix PM hours > 12
                    open, close = hours.split("-")
                    closeHour, closeMinute = close.split(":")
                    closeHour = int(closeHour)
                    if closeHour >= 12:
                        closeHour -= 12
                        close = f"{closeHour}:{closeMinute}"
                    hours = f"{open}-{close}"

                item["opening_hours"].add_ranges_from_string(f"{day} {hours}")

            if field["name"] == "Order Online":
                website_orders = field["value"]
                orders_query = parse_qs(urlparse(website_orders).query)
                if "$fallback_url" in orders_query:
                    website_orders = orders_query["$fallback_url"][0]
                item["extras"]["website:orders"] = website_orders

            if field["name"] == "Type" and field["value"] == "Licensed Partner":
                item["located_in"] = item.pop("name")

        item["branch"] = item.pop("name", None)

        features = {feature["name"] for feature in location["filters"]}
        apply_yes_no(PaymentMethods.CONTACTLESS, item, "Contactless Payments" in features)
        apply_yes_no("payment:gift_card", item, "Accepts Peet's Cards" in features)
        apply_yes_no(Extras.BREAKFAST, item, "Warm Breakfast" in features)
        apply_yes_no(Extras.WIFI, item, "Free Wi-Fi" in features)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in features)

        yield item
