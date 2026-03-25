import json
from typing import Iterable

import xmltodict
from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class HMVSpider(JSONBlobSpider):
    name = "hmv"
    item_attributes = {"brand": "HMV", "brand_wikidata": "Q10854572"}
    start_urls = ["https://hmv.com/api/stores?limitTo=3000&source=StoreFinder&type=1&postcode=Birmingham"]
    locations_key = ["StoreFinderResults", "Stores", "StoreFinderResult"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "hmv.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
        },
    }

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        data = xmltodict.parse(response.text)
        json_data = json.dumps(data)
        json_data = json.loads(json_data)
        print(json_data)
        if self.locations_key:
            if isinstance(self.locations_key, str):
                json_data = json_data[self.locations_key]
            elif isinstance(self.locations_key, list):
                for key in self.locations_key:
                    json_data = json_data[key]
        return json_data

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        print(feature)
        yield item
