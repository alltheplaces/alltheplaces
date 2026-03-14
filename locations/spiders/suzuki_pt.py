from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SuzukiPTSpider(Spider):
    name = "suzuki_pt"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    start_urls = ["https://www.suzukiauto.pt/concesionarios-lista"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["city"] = location.get("population")
            if location.get("tipo") == "Stand Vendas":  # Sales
                apply_category(Categories.SHOP_CAR, item)
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
