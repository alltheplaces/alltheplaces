import re

from locations.hours import DAYS, OpeningHours
from locations.items import set_closed
from locations.json_blob_spider import JSONBlobSpider


class MedexpressUSSpider(JSONBlobSpider):
    name = "medexpress_us"
    item_attributes = {"brand": "MedExpress", "brand_wikidata": "Q102183820"}
    start_urls = ["https://www.medexpress.com/bin/optum3/medexserviceCallToYEXT2"]
    locations_key = "locations"

    def post_process_item(self, item, response, location):
        if re.search("closed", location["locationName"], re.IGNORECASE):
            set_closed(item)

        item["street_address"] = item.pop("addr_full")
        if "Coming soon" in item["street_address"]:
            item.pop("street_address")
        if "displayWebsiteUrl" in location:
            item["website"] = location["displayWebsiteUrl"].split("?")[0]

        if location.get("hours"):
            item["opening_hours"] = OpeningHours()
            for rule in location.get("hours").split(","):
                day, start_hour, start_min, end_hour, end_min = rule.split(":")
                item["opening_hours"].add_range(
                    DAYS[int(day) - 2], "{}:{}".format(start_hour, start_min), "{}:{}".format(end_hour, end_min)
                )

        yield item
