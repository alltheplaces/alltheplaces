from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class PenningtonsCASpider(UberallSpider):
    name = "penningtons_ca"
    item_attributes = {
        "brand_wikidata": "Q16956527",
        "brand": "Penningtons",
    }
    key = "plEhL7SEWWjub5NBhsr8Iidzl8GgaX"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["ref"] = location["ref"].removeprefix("Store ")
        item["website"] = (
            f'https://locations.penningtons.com/{item["state"]}-{item["city"]}-{item["ref"]}'.lower().replace(" ", "-")
        )
        yield item
