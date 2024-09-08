import re

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

        # All of the Medexpress locations' hours are Mo-Su 08:00-20:00.
        if (
            "hours" in location
            and location["hours"]
            and location["hours"]
            == "1:8:00:20:00,2:8:00:20:00,3:8:00:20:00,4:8:00:20:00,5:8:00:20:00,6:8:00:20:00,7:8:00:20:00"
        ):
            item["opening_hours"] = "Mo-Su 08:00-20:00"

        yield item
