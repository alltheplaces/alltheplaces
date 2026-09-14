import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature, set_closed


class BellstoresUSSpider(Spider):
    name = "bellstores_us"
    item_attributes = {"brand": "BellStores", "brand_wikidata": "Q111698204", "name": "BellStores"}
    start_urls = ["https://bellstores.com/home/locations"]

    # Grades are only labelled ("Regular"/"Midgrade"/"Premium"/etc.), not given explicit octane numbers.
    unleaded_fuel_keys = (
        "HasFuelTypeRegular",
        "HasFuelTypeMidgrade",
        "HasFuelTypePremium",
        "HasFuelTypeMid1",
        "HasFuelTypeSuper2",
        "HasFuelTypeRec89",
        "HasFuelTypeRec90",
    )
    fast_food_keys = (
        "HasSubway",
        "HasDairyQueen",
        "HasDominosPizza",
        "HasHuntBrothersPizza",
        "HasChampsChicken",
        "HasChampsBreakfast",
    )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The store finder renders a Google Map from a JS array embedded in the page; there is no separate API.
        locations_blob = re.search(r"var locations = (\[.*\]);", response.text)
        for location in json.loads(locations_blob.group(1)):
            if location["StandAloneStore"]:
                # These are standalone Subway/Dairy Queen restaurants with no BellStores fuel or convenience
                # store on site, not BellStores locations themselves.
                continue

            item = Feature()
            item["ref"] = item["branch"] = location["Name"]
            item["street_address"] = location["Address1"]
            item["city"] = location["City"]
            item["state"] = location["State"]
            item["postcode"] = location["Zip"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            item["phone"] = location["PhoneNumber"]

            if location["isTemporarilyClosed"]:
                set_closed(item)

            apply_category(Categories.SHOP_CONVENIENCE, item)

            has_unleaded = any(location[key] for key in self.unleaded_fuel_keys)
            if has_unleaded or location["HasFuelTypeDiesel"] or location["HasFuelTypeKerosene"]:
                apply_category(Categories.FUEL_STATION, item)

            apply_yes_no(Fuel.GASOLINE, item, has_unleaded, False)
            apply_yes_no(Fuel.DIESEL, item, location["HasFuelTypeDiesel"], False)
            apply_yes_no(Fuel.KEROSENE, item, location["HasFuelTypeKerosene"], False)
            apply_yes_no(Fuel.ELECTRIC, item, location["HasEvCharging"], False)

            apply_yes_no(Extras.CAR_WASH, item, location["HasCarwash"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["HasDriveThru"], False)
            apply_yes_no(Extras.FAST_FOOD, item, any(location[key] for key in self.fast_food_keys), False)

            yield item
