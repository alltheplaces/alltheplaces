from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AGWarehouseAUSpider(Spider):
    name = "ag_warehouse_au"
    item_attributes = {"brand": "AG Warehouse", "brand_wikidata": "Q119261591"}
    allowed_domains = ["www.agwarehouse.com.au"]
    start_urls = ["https://www.agwarehouse.com.au/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = item["name"].strip()
            item["street_address"] = item.pop("street")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["open_hours"].replace("\\\"", "\"").replace("[", "").replace("]", ""))
            yield item
