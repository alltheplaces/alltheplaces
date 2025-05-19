from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class Rema1000DKSpider(Spider):
    name = "rema_1000_dk"
    item_attributes = {"brand": "Rema 1000", "brand_wikidata": "Q28459"}
    start_urls = ["https://cphapp.rema1000.dk/api/v3/stores?per_page=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("internal_id")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full", None)
            item["website"] = f'https://rema1000.dk/find-butik-og-abningstider/{item["ref"]}'
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
