from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class PetstockAUSpider(AlgoliaSpider):
    name = "petstock_au"
    item_attributes = {"brand": "Petstock", "brand_wikidata": "Q106540728"}
    api_key = "38ef8ba1d407151e9ca1c95adaa8d598"
    app_id = "SAZG66NOPD"
    index_name = "location_prod"
    referer = "https://www.petstock.com.au/"

    def pre_process_data(self, feature: dict):
        feature["ref"] = feature.pop("handle")
        feature["coordinates"] = feature.pop("_geoloc")
        feature["address"] = clean_address([feature.pop("addressLine1"), feature.pop("addressLine2")])
        feature["website"] = "https://www.petstock.com.au/store/" + feature["ref"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["isActive"] is not True:
            # Ignore closed locations.
            return

        if item["name"].startswith("Petstock "):
            item["branch"] = item.pop("name").removeprefix("Petstock ")

        if feature["services"]["isStore"] is True:
            apply_category(Categories.SHOP_PET, item)
        elif feature["services"]["isVetClinic"] is True:
            apply_category(Categories.VETERINARY, item)

        hours_string = " ".join(
            [
                day_hours["day"] + ": " + day_hours["openHours"]["open"] + "-" + day_hours["openHours"]["close"]
                for day_hours in feature["openingHours"]
            ]
        )
        day_pairs = [
            ["Monday", "Tuesday"],
            ["Tuesday", "Wednesday"],
            ["Wednesday", "Thursday"],
            ["Thursday", "Friday"],
            ["Friday", "Saturday"],
            ["Saturday", "Sunday"],
            ["Sunday", "Monday"],
        ]
        for day_pair in day_pairs:
            if day_pair[0] not in hours_string and day_pair[1] not in hours_string:
                hours_string = hours_string.replace("Today", day_pair[0]).replace("Tomorrow", day_pair[1])
                break
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
