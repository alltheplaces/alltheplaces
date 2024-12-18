import json
from typing import Any, Iterable

import scrapy
from scrapy import Request, Spider
from scrapy.http import Response, JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class SpeedwayUSSpider(Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    custom_settings = {"ROBOTSTXT_OBEY":False, "DOWNLOAD_TIMEOUT": 80}

    def make_request(self, offset: int, limit: int = 50) -> JsonRequest:
        url = "https://apis.7-eleven.com/v5/stores/graphql"
        data = ({
            "query": "query stores (\n      $brand: String,\n      $lat: String,\n      $lon: String,\n      $radius: Float,\n      $limit: Int,\n      $offset: Int,\n      $curr_lat: String,\n      $curr_lon: String,\n      $filters: [String])\n    {\n        stores (\n          brand: $brand,\n          lat: $lat,\n          lon: $lon,\n          radius: $radius,\n          limit: $limit,\n          offset: $offset,\n          curr_lat: $curr_lat,\n          curr_lon: $curr_lon,\n          filters: $filters)\n        {\n            id,\n            brand_id,\n            brand {\n                name\n            },\n            distance,\n            distance_label,\n            hours,\n            is_open_for_business,\n            address,\n            city,\n            phone,\n            state,\n            country,\n            postal_code,\n            lat,\n            lon,\n            fuel_data,\n            services\n            {\n                title,\n                slug\n            }\n        }\n    }",
            "variables": {
    "brand": "speedway",
    "radius": 2000000,
    "limit": 10000,
    "offset": 0,
    "lat": 36.778261,
    "lon": -119.4179324,
    "curr_lat": 36.778261,
    "curr_lon": -119.4179324,
    "filters": []
  }
})
        headers = {'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlRVMxb0xaSFpBeHRaVVNVOWtpbnpiVDFGMUk0RVYweFJVOTM1SVVCIiwic2NvcGUiOiJ3cml0ZV9wcm9maWxlIHJlYWRfY29uZmlnIiwiZ3JhbnRfdHlwZSI6ImNsaWVudF9jcmVkZW50aWFsIiwiZXhwIjoxNzM0NTc5OTA1LCJpYXQiOjE3MzQ0OTM1MDV9.gh6HYy_HZ-3l0n_h5CIASKzAdS9FDCoe1kGgB4Uq3Y20DjweBGdo2NtfObok5NShCmr-al_qK0mahiWu1E8NadWB-PXKmvyCqNFxHDQG69iKePPJmWbwLZ_SnmijSUYVXAszrNrQiFoDn08DeYQ6NV87CAVDUe44nlMSTQz9nFMm4nD4hf72a5KMeHYOonMR1SACowzkqsnkUd1BWCByQlmWpqWIZw2TP8is2vlT45PrOONaTGo-UlqSIg_3mFqH78EoK8OLvW8ZJUNSjFSMw3laHCxw4hB0huGbCGQTsBV_5pivVV9PnMjbwojAVs5e2ZUhszbLvwHCZQQT0fdH9w',
  'Content-Type': 'application/json',"Accept":"application/json, text/plain, */*"}



        return JsonRequest(url=url, method="POST",headers=headers,data=data,meta=dict(offset=offset, limit=limit))

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.speedway.com/"
            apply_category(Categories.FUEL_STATION,item)
            yield item
        yield self.make_request(response.meta["offset"] + response.meta["limit"])