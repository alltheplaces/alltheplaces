from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class SkyZoneSpider(Spider):
    name = "sky_zone"
    item_attributes = {"brand": "Sky Zone", "brand_wikidata": "Q7537557"}
    start_urls = ["https://skyzone.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = None
            item["street_address"] = merge_address_lines([location["address"], location["address2"]])
            item["branch"] = location["store"].removeprefix("DEFY ").removeprefix("Sky Zone ")
            item["website"] = location["park_url"]

            apply_category({"leisure": "trampoline_park"}, item)
            yield item
