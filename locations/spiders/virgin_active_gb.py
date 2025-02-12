from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES


class VirginActiveGBSpider(JSONBlobSpider):
    name = "virgin_active_gb"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    start_urls = ["https://www.virginactive.co.uk/api/club/getclubdetails"]
    locations_key = ["data", "clubs"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["clubId"]
        item["website"] = location["clubHomeUrl"]
        item["branch"] = item.pop("name")
        item["addr_full"] = location["compositeAddress"]

        item["opening_hours"] = OpeningHours()
        for day, times in location["openingHours"].items():
            if times.upper() == "CLOSED":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, times.split("-")[0], times.split("-")[1])
        yield item
