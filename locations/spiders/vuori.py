from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class VuoriSpider(Spider):
    name = "vuori"
    item_attributes = {"brand": "Vuori", "brand_wikidata": "Q121878733", "extras": Categories.SHOP_CLOTHES.value}
    start_urls = ["https://vuoriclothing.com/api/store-locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            if not location["isVuori"]:
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Vuori ")
            item["street_address"] = merge_address_lines(
                [location["address1"], location["address2"], location["address3"]]
            )
            if phones := location.get("phones"):
                item["phone"] = "; ".join(phones)

            yield item
