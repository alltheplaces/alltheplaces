import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BoniNLSpider(JSONBlobSpider):
    name = "boni_nl"
    start_urls = ["https://bonisupermarkt.nl/onze-winkels"]
    item_attributes = {"brand": "Boni", "brand_wikidata": "Q4380634"}

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = json.loads(response.xpath("/html/body/main/script[1]/text()").re_first(r"var stores = (\[.+?]);"))
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["email"] = feature["email_address"]
        item["website"] = "https://bonisupermarkt.nl/" + feature["label"]
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
