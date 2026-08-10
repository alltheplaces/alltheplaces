from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class TacoBellGBSpider(UberallSpider):
    name = "taco_bell_gb"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    key = "oeY9DoIkFdLIquGvE5IQNv9wW53kHs"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["website"] = "/".join(
            [
                "https://www.tacobell.co.uk/locations/l",
                item["city"].lower().replace(" ", "-"),
                location["streetAndNumber"].lower().replace(" ", "-"),
                str(location["id"]),
            ]
        )
        yield item
