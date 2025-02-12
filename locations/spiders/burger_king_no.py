from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingNOSpider(JSONBlobSpider):
    name = "burger_king_no"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://bk-no-ordering-api-fd-ebghbnd6ebadc7fz.z01.azurefd.net/api/v2/restaurants?latitude=65&longitude=11&radius=99900000&top=500"
    ]
    locations_key = "data"

    def pre_process_data(self, feature):
        feature.update(feature["storeLocation"].pop("coordinates"))

    def post_process_item(self, item, response, location):
        item["website"] = f"https://burgerking.no/restaurants/{location['slug']}"
        item["branch"] = item.pop("name")
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"], False)
        # apply_yes_no(Extras.WHEELCHAIR, item, location["hasWheelchairAccess"], False) # Always false, so not sure it is accurate
        # apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, location["hasDisabledToilets"], False) # Always false, so not sure it is accurate
        # apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location["hasBabyChanging"], False) # Always false, so not sure it is accurate
        # apply_yes_no(Extras.DELIVERY, item, location["isDeliveryAvailable"], False) # See below, which is what seems to be used by the website
        apply_yes_no(Extras.DELIVERY, item, location["isOrderingAvailable"], False)
        # apply_yes_no(Extras.TOILETS, item, location["hasToilets"], False) # Always false, so not sure it is accurate
        # apply_yes_no(Extras.WIFI, item, location["hasWiFi"]) # Always false, so not sure it is accurate

        yield JsonRequest(
            url=f"https://bk-no-ordering-api-fd-ebghbnd6ebadc7fz.z01.azurefd.net/api/v2/restaurants/{location['slug']}",
            callback=self.parse_store,
            meta={"item": item},
        )

    def parse_store(self, response):
        item = response.meta["item"]
        location = response.json()["data"]
        item["phone"] = location.get("storeContactNumber")
        item["email"] = location.get("storeEmailAddress")

        item["opening_hours"] = OpeningHours()
        for day in location["storeOpeningHours"]:
            item["opening_hours"].add_range(
                day["dayOfTheWeek"],
                day["hoursOfBusiness"]["opensAt"].split("T")[1],
                day["hoursOfBusiness"]["closesAt"].split("T")[1],
                time_format="%H:%M:%S",
            )

        yield item
