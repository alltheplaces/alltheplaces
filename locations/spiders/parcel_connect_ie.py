import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ParcelConnectIESpider(Spider):
    name = "parcel_connect_ie"
    start_urls = ["https://api.parcelconnect.ie/api/dropoff/get_All_county/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.json()["data"]):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = "Parcel Connect"

            yield item
