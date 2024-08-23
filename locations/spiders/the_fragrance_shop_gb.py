from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class TheFragranceShopGBSpider(Spider):
    name = "the_fragrance_shop_gb"
    item_attributes = {"brand": "The Fragrance Shop", "brand_wikidata": "Q105337125"}
    start_urls = ["https://www.thefragranceshop.co.uk/api/stores/all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            # TODO openingHours

            yield item
