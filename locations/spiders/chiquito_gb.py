from typing import Iterable

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class ChiquitoGBSpider(FrankieAndBennysGBSpider):
    name = "chiquito_gb"
    item_attributes = {"brand": "Chiquito", "brand_wikidata": "Q5101775"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/chiquito"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://www.chiquito.co.uk/restaurants/{}/{}/".format(location["city"], location["slug"])

        yield item
