from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TheBarreCodeUSSpider(StructuredDataSpider):
    name = "the_barre_code_us"
    item_attributes = {"brand": "The Barre Code", "brand_wikidata": "Q118870170"}
    start_urls = ["https://thebarrecode.com/"]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = item["website"]

        apply_category(Categories.GYM, item)
        yield item
