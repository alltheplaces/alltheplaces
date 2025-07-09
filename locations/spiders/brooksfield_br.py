import json
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class BrooksfieldBRSpider(JSONBlobSpider):
    name = "brooksfield_br"
    item_attributes = {"brand": "Brooksfield", "brand_wikidata": "Q3645372"}
    start_urls = ["https://www.brooksfield.com.br/onde-encontrar"]
    user_agent = BROWSER_DEFAULT

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = json.loads(
            response.xpath('//script[contains(text(), "wdPointOfSales")]/text()').re_first(r"wdPointOfSales = (\[.+]);")
        )
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["housenumber"] = feature.get("AddressNumber")
        item["ref"] = feature.pop("PointOfSaleID")
        yield item
