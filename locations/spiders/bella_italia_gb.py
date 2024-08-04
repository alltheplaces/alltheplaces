from typing import Iterable

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class BellaItaliaGBSpider(FrankieAndBennysGBSpider):
    name = "bella_italia_gb"
    item_attributes = {"brand": "Bella Italia", "brand_wikidata": "Q4883362"}
    start_urls = ["https://api.bigtablegroup.com/cdg/allRestaurants/bella"]

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://www.bellaitalia.co.uk/restaurants/{}/{}/".format(location["city"], location["slug"])

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        yield item
