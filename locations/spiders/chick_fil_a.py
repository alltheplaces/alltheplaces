from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext import YextSpider
from locations.structured_data_spider import clean_instagram, clean_twitter


class ChickfilASpider(YextSpider):
    name = "chick_fil_a"
    item_attributes = {"brand": "Chick-fil-A", "brand_wikidata": "Q491516"}
    api_key = "71620ba70d81b48c7c72331e25462ebc"
    wanted_types = ["restaurant"]

    def parse_item(self, item, location):
        if location.get("c_status") and location["c_status"] != "OPEN":
            return
        if location.get("c_locationName"):
            item["name"] = location["c_locationName"]
        if item["website"] and "?" in item["website"]:
            item["website"] = item["website"].split("?", 1)[0]
        item["twitter"] = clean_twitter(location.get("c_twitterURL"))
        item["extras"]["contact:instagram"] = clean_instagram(location.get("c_instagramURL"))
        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("c_hasDriveThru"), False)
        apply_yes_no(Extras.DELIVERY, item, location.get("c_offersDelivery"), False)
        apply_yes_no(Extras.INDOOR_SEATING, item, location.get("c_hasDiningRoom"), False)
        apply_yes_no(Extras.WIFI, item, location.get("c_offersWireless"), False)
        yield item
