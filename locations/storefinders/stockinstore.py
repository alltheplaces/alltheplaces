from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# To use this store locator, you need to determine whether the brand
# is using:
# 1. Widget to locate stores on a map
#    * Calls https://stockinstore.net/stores/getAllStores
# 2. Widget to find stock available in nearby stores
#    * Calls https://stockinstore.net/stores/getStoresForWidget
#    * or calls https://stockinstore.net/stores/getStoresStock
#
# Once you've found a relevant API call, you can then check the
# submitted form data for values to use for the mandatory API
# parameters "api_site_id" (5 digit number), "api_widget_id"
# (2 digit number) and "api_widget_type" (short string usually
# either "storelocator", "cnc", "sis" or "product").
#
# You also need to supply the mandatory API parameter "api_origin"
# which can be found be checking the submitted "Origin" HTTP header
# to the relevant API call. This will be the URL (without path) of
# the site where the widget is hosted e.g. https://brandexample.com


class StockInStoreSpider(Spider):
    dataset_attributes = {"source": "api", "api": "stockinstore.com"}
    api_site_id = None
    api_widget_id = None
    api_widget_type = None
    api_origin = None
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        data = {
            "site": self.api_site_id,
            "storeid": "",
            "widget": self.api_widget_id,
            "lang": "en-US",
            "widgetType": self.api_widget_type,
            "isajax": "1",
            "info": "none",
            "preview": "false",
        }
        yield FormRequest(
            url="https://stockinstore.net/stores/getAllStores",
            method="POST",
            headers={"Origin": self.api_origin},
            formdata=data,
        )

    def parse(self, response):
        for location in response.json()["response"]["stores_list"]:
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["street_address"] = " ".join(location["address_lines"])
            if not item.get("website"):
                item["website"] = location.get("store_locator_page_url")
            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["trading_hours_json"].items():
                item["opening_hours"].add_range(day_name, hours["open"], hours["close"], "%I:%M%p")
            yield from self.parse_item(item, location)

    def parse_item(self, item, location: {}, **kwargs):
        yield item
