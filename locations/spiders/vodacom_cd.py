from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.vodacom_za import VODACOM_SHARED_ATTRIBUTES


class VodacomCDSpider(JSONBlobSpider):
    name = "vodacom_cd"
    item_attributes = VODACOM_SHARED_ATTRIBUTES
    locations_key = ["response", "stores"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.vodacom.cd/integration/drcportal/store_locator/portal",
            data={"method": "findNearestStore", "longitude": 0, "latitude": 0, "source": "portal"},
        )

    def post_process_item(self, item, response, location):
        item["ref"] = location["_id"]
        item["branch"] = location.get("nameStructure")
        item["street_address"] = item.pop("addr_full")
        yield item
