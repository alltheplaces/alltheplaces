from scrapy import Request

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class ChestertonsGBSpider(JSONBlobSpider):
    name = "chestertons_gb"
    item_attributes = {
        "brand": "Chestertons",
        "brand_wikidata": "Q24298789",
    }

    def start_requests(self):
        yield Request("https://www.chestertons.co.uk/estate-agents", headers={"RSC": 1})

    def extract_json(self, response):
        return DictParser.get_nested_key(dict(parse_rsc(response.body)), "branches")

    def post_process_item(self, item, response, location):
        item["addr_full"] = location["displayAddress"]
        item["branch"] = item.pop("name")
        item["website"] = f"https://www.chestertons.co.uk/estate-agents/{location['slug']}"
        apply_category({"office": "estate_agent"}, item)
        yield item
