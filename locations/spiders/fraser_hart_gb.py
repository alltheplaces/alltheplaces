from typing import Iterable

import chompjs
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class FraserHartGBSpider(JSONBlobSpider):
    name = "fraser_hart_gb"
    item_attributes = {"brand": "Fraser Hart", "brand_wikidata": "Q134776549"}
    host = "core.service.elfsight.com"
    shop = "www.fraserhart.co.uk"
    api_key = "4a4f06f9-ddef-4c3e-a843-7ed8bb1de4c4"

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        yield JsonRequest(f"https://{self.host}/p/boot/?w={self.api_key}")

    def extract_json(self, response: Response) -> list:
        data = chompjs.parse_js_object(response.text)
        return data["data"]["widgets"][self.api_key]["data"]["settings"]["locations"]

    def pre_process_data(self, location: dict):
        location["lat"], location["lon"] = (
            location.get("place")["coordinates"]["lat"],
            location.get("place")["coordinates"]["lng"],
        )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("Fraser Hart, ").removesuffix(" - Fraser Hart")
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
