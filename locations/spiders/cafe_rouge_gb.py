from typing import Iterable
from urllib.parse import urljoin

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class CafeRougeGBSpider(FrankieAndBennysGBSpider):
    name = "cafe_rouge_gb"
    item_attributes = {"brand": "Café Rouge", "brand_wikidata": "Q5017261"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/rouge"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = urljoin(
            "https://www.caferouge.com/restaurants/", "/".join([location["city"], location["slug"]])
        )
        yield item
