from locations.categories import Extras, apply_yes_no
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
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"], False)
        # apply_yes_no(Extras.WHEELCHAIR, item, location["hasWheelchairAccess"], False) # Always false, not sure it is accurate
        # apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, location["hasDisabledToilets"], False) # Always false, not sure it is accurate
        # apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location["hasBabyChanging"], False) # Always false, not sure it is accurate
        # apply_yes_no(Extras.DELIVERY, item, location["isDeliveryAvailable"], False) # See below, which is what seems to be used by the website
        apply_yes_no(Extras.DELIVERY, item, location["isOrderingAvailable"], False)
        # apply_yes_no(Extras.TOILETS, item, location["hasToilets"], False) # Always false, not sure it is accurate
        # apply_yes_no(Extras.WIFI, item, location["hasWiFi"]) # Always false, not sure it is accurate
        yield item
