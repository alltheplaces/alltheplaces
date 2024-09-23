from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GroceryOutletUSSpider(Spider):
    name = "grocery_outlet_us"
    item_attributes = {"brand": "Grocery Outlet", "brand_wikidata": "Q5609934"}

    def start_requests(self):
        yield FormRequest(
            "https://www.groceryoutlet.com/wp-admin/admin-ajax.php", formdata={"action": "get_store_list"}
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["ref"] = location["store_number"]
            item["extras"]["start_date"] = location["open_date"]
            item["facebook"] = location["fb_url"]

            oh = OpeningHours()
            oh.add_ranges_from_string(f"Mo-Fr {location['hoursMF']}")
            oh.add_ranges_from_string(f"Sa {location['hoursSat']}")
            oh.add_ranges_from_string(f"Su {location['hoursSun']}")
            item["opening_hours"] = oh

            yield item
