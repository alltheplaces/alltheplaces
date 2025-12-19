from typing import Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CinemexMXSpider(JSONBlobSpider):
    name = "cinemex_mx"
    item_attributes = {"brand": "Cinemex", "brand_wikidata": "Q3333072"}
    start_urls = ["https://www.cinemex.com/"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "cinemas=")]/text()').re_first(r"(?<=cinemas=).*states\b")
        )
        return json_data

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("info"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["state"] = feature["state"]["name"]
        item["city"] = feature["area"]["name"]
        item["website"] = f'https://cinemex.com/cine/{item["ref"]}/{item["branch"].lower().replace(" ", "-")}'
        apply_category(Categories.CINEMA, item)
        yield item
