from chompjs import parse_js_object
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TyreplusAUSpider(JSONBlobSpider):
    name = "tyreplus_au"
    item_attributes = {"brand": "Tyreplus", "brand_wikidata": "Q110959120"}
    allowed_domains = ["www.tyreplus.com.au"]
    start_urls = ["https://www.tyreplus.com.au/tyre-shop"]

    def extract_json(self, response: Response) -> list[dict]:
        js_blob = response.xpath('//script[contains(text(), "markers")]/text()').get()
        js_blob = "[" + js_blob.split('\\"markers\\":[', 1)[1].split(']},\\"clusters\\":', 1)[0] + "]"
        js_blob = js_blob.replace('\\"', '"')
        features = parse_js_object(js_blob)
        return features

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("idFitter", None)
        feature["website"] = feature["marker"].pop("url", None)
        feature["phone"] = feature.pop("telCallDN", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Tyreplus ").removeprefix("TYREPLUS ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
