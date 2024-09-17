from typing import Iterable

from chompjs import parse_js_object
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AsianPaintsBeautifulHomesINSpider(JSONBlobSpider):
    name = "asian_paints_beautiful_homes_in"
    item_attributes = {
        "brand": "Asian Paints Beautiful Homes",
        "brand_wikidata": "Q130310105",
        "extras": Categories.SHOP_INTERIOR_DECORATION.value,
    }
    allowed_domains = ["www.beautifulhomes.asianpaints.com"]
    start_urls = [
        "https://www.beautifulhomes.asianpaints.com/content/asianpaintsbeautifulhomes/asianpaintsbeautifulhomesapi/storespostapi.json"
    ]
    locations_keys = "result"

    def start_requests(self) -> Iterable[Request]:
        # Scrapy doens't support multipart/form-data which this API requires.
        # Reference: https://github.com/scrapy/scrapy/issues/1897
        multipart_data = '-----------------------------524311191360322593742077878\r\nContent-Disposition: form-data; name="data"\r\n\r\n{"data":{"searchpath":"/content/asianpaintsbeautifulhomes/us/en/store-locator","limit":""},"headerJson":{}}\r\n-----------------------------524311191360322593742077878--\r\n'
        headers = {
            "Content-Type": "multipart/form-data; boundary=---------------------------524311191360322593742077878"
        }
        yield Request(url=self.start_urls[0], headers=headers, body=multipart_data, method="POST")

    def extract_json(self, response: Response) -> list:
        # Data contains invalid non UTF-8 codepoints. chompjs' parse_js_object
        # can handle this mess.
        json_data = parse_js_object(response.text)
        return json_data["result"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        print(feature)
        item["ref"] = feature["pincode"]
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.strip().removesuffix(" | Beautiful Homes").removeprefix("AP Beautiful Homes ")
        item["lat"], item["lon"] = url_to_coords(feature["lat_long"])
        yield item
