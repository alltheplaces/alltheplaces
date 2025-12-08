import re

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlGBSpider(VirtualEarthSpider):
    name = "lidl_gb"
    item_attributes = {
        "brand": "Lidl",
        "brand_wikidata": "Q151954",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }

    dataset_id = "588775718a4b4312842f6dffb4428cff"
    dataset_name = "Filialdaten-UK/Filialdaten-UK"
    api_key = "Argt0lKZTug_IDWKC5e8MWmasZYNJPRs0btLw62Vnwd7VLxhOxFLW2GfwAhMK5Xg"

    def parse_item(self, item, feature, **kwargs):
        if match := re.match(r"(\w{1,2}\d{1,2}\w?) (\d|O)(\w{2})", feature["Locality"].upper()):
            if match.group(2) == "O":
                item["postcode"] = f"{match.group(1)} 0{match.group(3)}"
            else:
                item["postcode"] = f"{match.group(1)} {match.group(2)}{match.group(3)}"
            item["city"] = feature["PostalCode"]
        else:
            item["postcode"] = feature["PostalCode"]
            item["city"] = feature["Locality"]

        item["opening_hours"] = self.parse_opening_hours(feature["OpeningTimes"])

        apply_category(Categories.SHOP_SUPERMARKET, item)

        if feature["INFOICON17"] == "customerToilet":
            item["extras"]["toilets"] = "yes"
            item["extras"]["toilets:access"] = "customers"

        yield item

    def parse_opening_hours(self, opening_times: str) -> OpeningHours:
        oh = OpeningHours()

        for day, hours in re.findall(r">(\w\w) {3}(.+?)(?:<|$)", opening_times):
            if hours == "Closed":
                oh.set_closed(day)
            else:
                oh.add_range(day, *hours.split("-"))

        return oh
