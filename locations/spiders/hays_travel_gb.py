from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class HaysTravelGBSpider(UberallSpider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    key = "xKkPXW8KuKiZLOaOUiIWZ2ckdz7nsz"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Hays Travel ")
        item["website"] = f'https://www.haystravel.co.uk/branches/{item["branch"].lower().replace(" ","-")}/'
        yield item
