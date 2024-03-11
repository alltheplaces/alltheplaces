from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# To use, specify the Shopify URL for the brand in the format of
# {brand-name}.myshopify.com . You may then need to override the
# parse_item function to adjust extracted field values.


class MetizsoftSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "storelocator.metizapps.com"}
    shopify_url: str = ""
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/storelocator\.metizapps\.com\/stores\/storeDataGet$", data=r'{"shopify_url": .shopData}'
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/storelocator\.metizapps\.com\/assets\/js\/app\.js\?shop=(?P<shopify_url>[A-Za-z0-9\-.]+)$"
        ),
    ]

    def start_requests(self):
        yield FormRequest(
            url="https://storelocator.metizapps.com/stores/storeDataGet",
            method="POST",
            formdata={"shopData": self.shopify_url},
        )

    def parse(self, response: Response):
        if not response.json()["success"]:
            return

        for location in response.json()["data"]["result"]:
            if location["delete_status"] != "0" or location["storestatus"] != "1":
                continue
            item = DictParser.parse(location)
            item["street_address"] = ", ".join(filter(None, [location["address"], location["address2"]]))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["hour_of_operation"].replace("</br>", " "))
            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict):
        yield item
