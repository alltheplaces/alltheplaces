from typing import Iterable

import chompjs
from scrapy.http import JsonRequest, Request

from locations.json_blob_spider import JSONBlobSpider


class ElfsightSpider(JSONBlobSpider):
    """
    An Elfsight spider will be one of:
    - https://shy.elfsight.com/p/boot/?callback=a&shop=(shop)&w=(api_key)
    - https://core.service.elfsight.com/p/boot/?w=(api_key)
    """
    host = None
    shop = None
    api_key = None

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(f"https://{self.host}/p/boot/?callback=a&shop={self.shop}&w={self.api_key}")

    def extract_json(self, response):
        data = chompjs.parse_js_object(response.text)
        return data["data"]["widgets"][self.api_key]["data"]["settings"]["markers"]

    def pre_process_data(self, location):
        location["addr"] = location.pop("infoAddress")
        location["phone"] = location.pop("infoPhone")
        location["email"] = location.pop("infoEmail")
        location["lat"], location["lon"] = location.get("coordinates").split(", ", 1)
