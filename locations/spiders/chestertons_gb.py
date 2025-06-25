from typing import Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class ChestertonsGBSpider(JSONBlobSpider):
    name = "chestertons_gb"
    item_attributes = {"brand": "Chestertons", "brand_wikidata": "Q24298789"}

    def start_requests(self):
        yield Request("https://www.chestertons.co.uk/estate-agents", headers={"RSC": 1})

    def extract_json(self, response):
        return DictParser.get_nested_key(dict(parse_rsc(response.body)), "branches")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = feature["displayAddress"]
        item["website"] = urljoin("https://www.chestertons.co.uk/estate-agents/", feature["slug"])

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)

        yield item
