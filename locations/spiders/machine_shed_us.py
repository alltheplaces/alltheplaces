from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MachineShedUSSpider(StructuredDataSpider):
    name = "machine_shed_us"
    item_attributes = {"name": "Machine Shed"}
    start_urls = [
        "https://machineshed.com/appleton/",
        "https://machineshed.com/davenport/",
        "https://machineshed.com/pewaukee/",
        "https://machineshed.com/rockford/",
        "https://machineshed.com/urbandale/",
    ]
    wanted_types = ["Restaurant"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").removeprefix("Machine Shed Restaurant ")

        apply_category(Categories.RESTAURANT, item)

        yield item
