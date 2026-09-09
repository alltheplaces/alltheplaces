from typing import Iterable

from scrapy.http import Response

from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class YourMoveGBSpider(StructuredDataSpider):
    name = "your_move_gb"
    item_attributes = {"brand": "Your Move", "brand_wikidata": "Q81078416"}
    start_urls = ["https://www.your-move.co.uk/branches"]
    wanted_types = ["RealEstateAgent"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # A single ld+json blob holds an ItemList of RealEstateAgent branches
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("@type") == "ItemList":
                yield from ld_obj.get("itemListElement", [])

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        if image := ld_data.get("image", {}).get("url"):
            item["image"] = image
        item["ref"] = item["website"].split("/")[-1]
        yield item
