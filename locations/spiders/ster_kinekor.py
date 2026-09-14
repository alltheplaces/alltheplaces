import json
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SterKinekorSpider(JSONBlobSpider):
    name = "ster_kinekor"
    item_attributes = {"brand": "Ster-Kinekor", "brand_wikidata": "Q130179"}
    start_urls = ["https://www.sterkinekor.com/locator"]

    def extract_json(self, response: Response) -> list[dict]:
        blob = response.xpath('//script[contains(., "_blockName") and contains(., "cinemas")]/text()').re_first(
            r'decodeURIComponent\("([^"]+)"\)'
        )
        return json.loads(unquote(blob))["cinemas"]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.sterkinekor.com/cinemas/" + location["linkToPage"]
        item.pop("phone", None)
        apply_category(Categories.CINEMA, item)
        yield item
