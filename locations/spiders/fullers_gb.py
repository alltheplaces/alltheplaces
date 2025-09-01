import json

from typing import Iterable, Any

from scrapy.http import FormRequest, Response
from scrapy.spiders import Request

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT
from locations.structured_data_spider import StructuredDataSpider

class FullersGBSpider(JSONBlobSpider,StructuredDataSpider):
    name = "fullers_gb"
    item_attributes = {
        "brand": "Fullers",
        "brand_wikidata": "Q5253950",
    }

    custom_settings = {
        "COOKIES_ENABLED": True,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    locations_key = ['items']
    wanted_types = ['restaurant']

    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url = "https://www.fullers.co.uk/api/main/pubs/feed",
            formdata = {
                "pageNumber":str(page),
                "latitude":"0",
                "longitude":"0",
                "categories":[],
                "area":""#D61B5F3C29994C99A3C93FA4144315A9"
            },
            method="POST",
            headers = {
                "Host": "www.fullers.co.uk",
                "Accept": "application/json",
            },
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response) -> Iterable[Feature]:
        features = self.extract_json(response)
        for feature in features:
            if feature["link"]:
                yield Request(url=feature["link"], callback=self.parse_sd)
            else:
                if feature is None:
                    continue
                feature["id"] = feature["pubId"]
                item = DictParser.parse(feature)
                yield from self.post_process_item_json(item, response, feature) or []

        if response.json()["totalPages"] > response.json()["currentPage"]:
            yield self.make_request(int(response.json()["currentPage"]) + 1)

    def post_process_item_json(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["subTitle"]:
            item["addr_full"] = feature["subTitle"]
        if feature["link"]:
            item["website"] = feature["link"]
        yield item
