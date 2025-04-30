import re
from typing import Any, Iterable

import scrapy
from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SpeedwayUSSpider(Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 210}

    def start_requests(self) -> Iterable[Request]:
        yield scrapy.Request(url="https://www.speedway.com/locations", callback=self.parse_cookies)

    def parse_cookies(self, response, **kwargs):
        for token_string in response.headers.getlist("Set-Cookie"):
            if "accessToken" not in str(token_string):
                continue
            token = re.search(r"accessToken%22%3A%22(.*)%22%7D;", str(token_string)).group(1)
            url = "https://apis.7-eleven.com/v5/stores/graphql"
            query = """query stores(
  $brand: String,
  $lat: String,
  $lon: String,
  $radius: Float,
  $limit: Int,
  $offset: Int,
  $curr_lat: String,
  $curr_lon: String,
  $filters: [String]
) {
  stores(
    brand: $brand,
    lat: $lat,
    lon: $lon,
    radius: $radius,
    limit: $limit,
    offset: $offset,
    curr_lat: $curr_lat,
    curr_lon: $curr_lon,
    filters: $filters
  ) {
    id
    brand_id
    brand {
      name
    }
    distance
    distance_label
    hours
    is_open_for_business
    address
    city
    phone
    state
    country
    postal_code
    lat
    lon
    fuel_data
    services {
      title
      slug
    }
  }
}
"""
            data = {
                "query": query,
                "variables": {
                    "brand": "speedway",
                    "radius": 2000000,
                    "limit": 4000,
                    "offset": 0,
                    "lat": 36.778261,
                    "lon": -119.4179324,
                    "curr_lat": 36.778261,
                    "curr_lon": -119.4179324,
                    "filters": [],
                },
            }
            headers = {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
            }
            yield JsonRequest(url=url, method="POST", headers=headers, data=data, callback=self.parse_details)

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.speedway.com/"
            apply_category(Categories.FUEL_STATION, item)
            yield item
