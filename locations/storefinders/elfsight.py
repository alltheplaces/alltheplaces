import chompjs

from locations.json_blob_spider import JSONBlobSpider
from typing import Iterable

from scrapy.http import JsonRequest, Request, Response



class ElfsightSpider(JSONBlobSpider):
    host = None
    shop = None
    api_key = None

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(f"https://{self.host}/p/boot/?callback=a&shop={self.shop}&w={self.api_key}")

    def extract_json(self, response):
        data = chompjs.parse_js_object(response.text)
        return data["data"]["widgets"][self.api_key]["data"]["settings"]["markers"]