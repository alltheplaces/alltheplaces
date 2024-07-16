from typing import Iterable

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class LasIguanasGBSpider(FrankieAndBennysGBSpider):
    name = "las_iguanas_gb"
    item_attributes = {"brand": "Las Iguanas", "brand_wikidata": "Q19875012"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/iguanas"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://www.iguanas.co.uk/restaurants/{}/".format(location["slug"])
        yield item
