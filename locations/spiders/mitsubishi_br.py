from copy import deepcopy
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MitsubishiBRSpider(scrapy.Spider):
    name = "mitsubishi_br"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://api.mitsubishimotors.com.br/search/api/dealer/v1.0/nearest?page=0&size=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for dealer in response.json().get("results", []):
            item = DictParser.parse(dealer)
            item["branch"] = item.pop("name")
            website = dealer.get("website")
            if website and not website.startswith("https"):
                item["website"] = "https://" + website.strip()

            if dealer.get("newCars"):
                sales_item = deepcopy(item)
                sales_item["ref"] = f"{item['ref']}-sales"
                apply_category(Categories.SHOP_CAR, sales_item)
                apply_yes_no(Extras.CAR_REPAIR, sales_item, dealer.get("postSalesServices"))
                apply_yes_no(Extras.USED_CAR_SALES, sales_item, dealer.get("nearlyNewCars"))
                apply_yes_no(Extras.CAR_PARTS, sales_item, dealer.get("kitCarParts"))
                yield sales_item

            if dealer.get("postSalesServices"):
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                apply_yes_no(Extras.CAR_PARTS, service_item, dealer.get("kitCarParts"))
                yield service_item
