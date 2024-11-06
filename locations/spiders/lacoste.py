from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import FIREFOX_LATEST


class LacosteSpider(JSONBlobSpider):
    name = "lacoste"
    item_attributes = {"brand": "Lacoste", "brand_wikidata": "Q309031"}
    start_urls = [
        "https://www.lacoste.com/fr/stores?maxLatitude=90&minLatitude=-90&maxLongitude=180&minLongitude=-180&json=true"
    ]
    user_agent = FIREFOX_LATEST

    def extract_json(self, response: Response) -> list:
        return response.json()["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["website"] = f'https://www.lacoste.com/fr/stores{feature["url"]}'
        country = feature["url"].split("/")[1]
        if "taiwan" in country:
            item["country"] = "TW"
        elif country.startswith("china"):
            item["country"] = "CN"
        else:
            item["country"] = country.title()
        yield item
