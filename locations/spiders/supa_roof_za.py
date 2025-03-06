from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class SupaRoofZASpider(JSONBlobSpider):
    name = "supa_roof_za"
    start_urls = ["https://shop.suparoof.co.za/storefinder"]
    item_attributes = {
        "brand": "Supa-Roof",
        "brand_wikidata": "Q116474839",
    }

    def extract_json(self, response: Response) -> dict | list[dict]:
        return [
            chompjs.parse_js_object(region)
            for region in response.xpath('//script[contains(text(), "let region")]/text()').getall()
        ]

    def pre_process_data(self, feature: dict) -> None:
        feature["address"] = merge_address_lines([feature.pop("address_line1", ""), feature.pop("address_line2", "")])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = f'https://shop.suparoof.co.za/storefinder/store/index/id/{item["ref"]}/'
        yield item
