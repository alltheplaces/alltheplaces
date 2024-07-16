from typing import Iterable

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class BananaTreeGBSpider(FrankieAndBennysGBSpider):
    name = "banana_tree_gb"
    item_attributes = {"brand": "Banana Tree", "brand_wikidata": "Q123013837"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/banana"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://bananatree.co.uk/restaurants/{}/".format(location["slug"])

        yield item
