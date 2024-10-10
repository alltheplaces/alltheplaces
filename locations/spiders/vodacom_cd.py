from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider


class VodacomCDSpider(JSONBlobSpider):
    name = "vodacom_cd"
    item_attributes = item_attributes = {
        "brand": "Vodacom Congo",
        "brand_wikidata": "Q130477507",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
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
