from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class SmythstoysGBSpider(Spider):
    name = "smythstoys_gb"
    item_attributes = {"brand": "SmythsToys", "brand_wikidata": "Q7546779"}
    start_urls = ["https://www.smythstoys.com/uk/en-gb/store-finder/getAllStores"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["data"]:
            for store in region["regionPos"]:
                item = DictParser.parse(store)
                item["branch"] = item.pop("name")
                item["street_address"] = merge_address_lines([item["street_address"], store["line2"], store["line3"]])

                # TODO: Opening hours

                yield item
