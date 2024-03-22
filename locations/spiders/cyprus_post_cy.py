from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class CyprusPostCYSpider(Spider):
    name = "cyprus_post_cy"
    item_attributes = {"brand": "Cyprus Post", "brand_wikidata": "Q5200484"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.cypruspost.post/maps/ajax/get-locations/1", headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            if location["name"].startswith("Parcel24"):
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["name"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]

            apply_category(Categories.POST_OFFICE, item)

            yield item
