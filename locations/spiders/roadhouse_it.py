from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class RoadhouseITSpider(UberallSpider):
    name = "roadhouse_it"
    item_attributes = {"brand": "Roadhouse", "brand_wikidata": "Q7339591"}
    key = "N5T07dDctgwa1W7reJjeQefV1Mnnj0"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["ref"] = location["id"]
        item["branch"] = (
            item.pop("name")
            .removeprefix("ROADHOUSE RESTAURANT ")
            .removeprefix("Roadhouse Restaurant ")
            .removeprefix("Roadhouse ")
            .strip(" -")
        )
        item["website"] = "/".join(
            [
                "https://www.roadhouse.it/store-locator/#!/l",
                item["city"],
                item["street_address"].replace(" ", "-"),
                str(item["ref"]),
            ]
        )
        yield item
