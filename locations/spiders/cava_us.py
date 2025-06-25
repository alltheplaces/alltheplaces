import json

from scrapy.http import Response

from locations.dict_parser import DictParser
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
