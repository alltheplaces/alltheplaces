import json
from typing import Iterable

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CavaUSSpider(JSONBlobSpider):
    name = "cava_us"
    item_attributes = {"brand": "CAVA", "brand_wikidata": "Q85751038"}
    start_urls = ["https://cava.com/locations"]

    def extract_json(self, response: Response) -> list[dict]:
        return DictParser.get_nested_key(
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()), "stores"
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("geographic", {}))
        feature.update(feature.pop("address", {}))
        feature["address"] = feature.pop("primary", {})
        feature.update(feature.pop("communication", {}))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("storeNumber")
        item["branch"] = item.pop("name", "")
        item["phone"] = feature.get("telephones", {}).get("primary", {}).get("number")
        item["email"] = feature.get("emailAddresses", {}).get("primary", {}).get("address")
        item["website"] = f'{response.url}/{feature.get("locationRef")}'
        yield item
