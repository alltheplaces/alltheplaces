from typing import AsyncIterator, Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HesburgerSpider(JSONBlobSpider):
    name = "hesburger"
    item_attributes = {"brand": "Hesburger", "brand_wikidata": "Q1276832"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country in ["fi", "ee", "lv", "lt", "de", "bg", "ua"]:
            yield JsonRequest(
                url=f"https://www.hesburger.com/restaurants?country={country}",
            )

    def extract_json(self, response: Response) -> dict | list[dict]:
        store_details = parse_js_object(response.xpath('//script[contains(text(), "var DATA")]/text()').get())
        return store_details

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["nimi"].replace("Hesburger ", "").replace("HESBURGER ", "")
        item["ref"] = feature["tid"]
        item["addr_full"] = feature["osoite"]
        apply_category(Categories.FAST_FOOD, item)
        yield item
