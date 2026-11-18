import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class TopsAtSparSpider(Spider):
    name = "tops_at_spar"
    item_attributes = {"brand": "Tops at Spar", "brand_wikidata": "Q116377563"}
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.topsatspar.co.za/api/stores/search",
            data={"SearchText": "", "Types": ["TOPS"], "Services": []},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            location["location"] = {"lat": location["GPSLat"], "lon": location["GPSLong"]}
            location["street_address"] = location["PhysicalAddress"]
            location["address"] = merge_address_lines(
                [location["PhysicalAddress"], location["Suburb"], location["Town"]]
            )
            location["Url"] = f'https://www.topsatspar.co.za/{location["Url"]}'

            item = DictParser.parse(location)
            item["branch"] = re.sub(r"(?i)^tops(?:\s+at|\s*@)?\s+|\s+tops\b", "", item.pop("name"))
            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
