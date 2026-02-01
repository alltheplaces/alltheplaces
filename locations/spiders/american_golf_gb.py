import json
import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class AmericanGolfGBSpider(JSONBlobSpider):
    name = "american_golf_gb"
    item_attributes = {"brand": "American Golf", "brand_wikidata": "Q62657494"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.americangolf.co.uk/en/find-stores/",
    ]

    def extract_json(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"channel\":(\[.*\]),\"p1BadgeData",
                response.xpath('//*[contains(text(),"address1")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        return raw_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = feature["listAddress"]
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        yield item
