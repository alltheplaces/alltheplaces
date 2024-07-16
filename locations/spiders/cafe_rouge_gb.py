from typing import Iterable

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class CafeRougeGBSpider(FrankieAndBennysGBSpider):
    name = "cafe_rouge_gb"
    item_attributes = {"brand": "Café Rouge", "brand_wikidata": "Q5017261"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/rouge"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://www.caferouge.com/restaurants/{}/{}/".format(location["city"], location["slug"])

        yield item
