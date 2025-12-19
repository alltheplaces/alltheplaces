from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.closeby import ClosebySpider


class TahinisCASpider(ClosebySpider):
    name = "tahinis_ca"
    item_attributes = {"brand": "Tahini's", "brand_wikidata": "Q135991974"}
    api_key = "683ae655cc7607037419c31e18678d08"

    def pre_process_data(self, feature: dict):
        feature["geometry"]["coordinates"] = feature["geometry"]["coordinates"][:2]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = None
        item["branch"] = item.pop("name").removeprefix("Tahini's ")

        yield item
