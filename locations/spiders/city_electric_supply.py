import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CityElectricSupplySpider(Spider):
    name = "city_electric_supply"
    item_attributes = {"brand": "City Electric Supply", "brand_wikidata": "Q121357206"}
    start_urls = ["https://www.cityelectricsupply.com/branchlocator", "https://www.cityelectricsupply.ca/branchlocator"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := re.search(r"var jsonAllBranches = (\[.+\]);", response.text):
            for location in json.loads(data.group(1)):
                item = DictParser.parse(location)
                item["unit"] = location["Address2"]
                item["name"] = location["BranchName"]
                item["ref"] = location["BranchId"]
                item["website"] = response.urljoin(f'/branch/{location["BranchId"]}')
                apply_category(Categories.SHOP_ELECTRICAL, item)

                yield item
