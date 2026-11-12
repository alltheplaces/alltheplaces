from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ToolstationBENLSpider(StructuredDataSpider):
    name = "toolstation_be_nl"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    start_urls = ["https://www.toolstation.nl/branches", "https://www.toolstation.be/branches"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if "nl" in response.url:
            item["website"] = f'https://www.toolstation.nl/branches/{item["branch"]}'
        else:
            item["website"] = f'https://www.toolstation.be/branches/{item["branch"]}'
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
