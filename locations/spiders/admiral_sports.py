from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class AdmiralSportsSpider(scrapy.Spider):
    name = "admiral_sports"
    item_attributes = {"brand": "Admiral Sports", "brand_wikidata": "Q4683720"}
    locations_key = ["data", "mc_asl_list", "items"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://payment.admiralsports.shop/graphql",
            headers={"Referer": "https://www.admiralsports.shop/"},
            data={
                "query": """
    query ($lat: String!, $lng: String!, $radius: Float!, $sku: String!, $category: Int!) {
        mc_asl_list(lat: $lat, lng: $lng, radius: $radius, sku: $sku, category: $category) {
            currentStoreId
            totalRecords
            items {
                id
                name
                address
                city
                state
                country
                zip
                lat
                lng
                phone
                email
                website
                description
                short_description
                schedule_string
                canonical_url
                url_key
            }
        }
    }
    """,
                "variables": {"lat": "37.977154", "lng": "23.673395", "radius": 0.0, "sku": "0", "category": 0},
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["mc_asl_list"]["items"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            yield item
