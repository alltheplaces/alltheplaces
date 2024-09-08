from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.sunglass_hut_1 import SUNGLASS_HUT_SHARED_ATTRIBUTES


class SunglassHutINSpider(JSONBlobSpider):
    name = "sunglass_hut_in"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    start_urls = ["https://sunglasshut.in/api/service/application/catalog/v1.0/locations/?page_size=100000"]
    locations_key = "items"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers={"authorization": "Bearer NjJlYjM3NTM1Zjk2NzkyOWRhY2EwM2UzOkZLX0dnVll3NA=="},
                callback=self.parse,
            )

    def post_process_item(self, item, response, location):
        item["lon"], item["lat"] = location["lat_long"]["coordinates"]
        item["branch"] = item.pop("name")
        item["postcode"] = location.get("pincode")
        item["street_address"] = item.pop("addr_full")
        phone = [i for i in location["contacts"] if "number" in i.keys()][0]
        item["phone"] = f"+{phone['country_code']} {phone['number']}"
        yield item
