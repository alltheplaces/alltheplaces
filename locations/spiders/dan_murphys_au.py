from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class DanMurphysAUSpider(Spider):
    name = "dan_murphys_au"
    item_attributes = {"brand": "Dan Murphy's", "brand_wikidata": "Q5214075"}
    allowed_domains = ["store.danmurphys.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.danmurphys.com.au/stores/all-stores"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest("https://api.danmurphys.com.au/apis/ui/StoreLocator/Stores/bws")

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["AddressLine1"], location["AddressLine2"]])
            item["ref"] = location["Id"]
            slug = "{}-{}-{}".format(location["State"], location["Suburb"].replace(" ", "-"), item["ref"])
            item["website"] = urljoin("https://danmurphys.com.au/stores/", slug)

            # TODO: TradingHours

            yield item
