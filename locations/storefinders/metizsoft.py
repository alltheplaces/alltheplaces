from chompjs import parse_js_object
from urllib.parse import parse_qs, urlparse

from scrapy import Spider
from scrapy.http import FormRequest, Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# To use, specify the Shopify URL for the brand in the format of
# {brand-name}.myshopify.com . You may then need to override the
# parse_item function to adjust extracted field values.


class MetizsoftSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "storelocator.metizapps.com"}
    shopify_url = ""

    def start_requests(self):
        yield FormRequest(
            url="https://storelocator.metizapps.com/stores/storeDataGet",
            method="POST",
            formdata={"shopData": self.shopify_url},
        )

    def parse(self, response, **kwargs):
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

    def parse_item(self, item, location: {}, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool | Request:
        js_blob = response.xpath('//script[contains(text(), "function asyncLoad() {")]/text()').get()
        js_blob = "[" + js_blob.split("var urls = [", 1)[1].split("];", 1)[0] + "]"
        urls = parse_js_object(js_blob)
        for url in urls:
            if urlparse(url).netloc == "storelocator.metizapps.com":
                return True
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict | Request:
        js_blob = response.xpath('//script[contains(text(), "function asyncLoad() {")]/text()').get()
        js_blob = "[" + js_blob.split("var urls = [", 1)[1].split("];", 1)[0] + "]"
        urls = parse_js_object(js_blob)
        for url in urls:
            if urlparse(url).netloc == "storelocator.metizapps.com":
                for argument_key, argument_value in parse_qs(urlparse(url).query).items():
                    if argument_key == "shop":
                        return {"shopify_url": argument_value[0]}
        return {}
