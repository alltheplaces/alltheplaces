from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.items import Feature


class CancerResearchUkGBSpider(Spider):
    name = "cancer_research_uk_gb"
    item_attributes = {"brand": "Cancer Research UK", "brand_wikidata": "Q326079", "country": "GB"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://find.cancerresearchuk.org/api/search",
            data={"state": {"current": page, "resultsPerPage": 100}, "searchKey": "shops"},
            cb_kwargs={"current_page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["results"]:
            item = Feature()
            item["addr_full"] = location["shop_address"]["raw"]
            item["phone"] = location.get("shop_phone_number", {}).get("raw")
            item["postcode"] = location["postcode"]["raw"]
            item["branch"] = location["title"]["raw"]
            item["website"] = location["url"]["raw"]
            item["ref"] = location["id"]["raw"]

            yield scrapy.Request(
                url=item["website"],
                callback=self.parse_lat_lon,
                meta={"item": item},
            )

        if kwargs["current_page"] <= response.json()["totalPages"]:
            yield self.make_request(kwargs["current_page"] + 1)

    def parse_lat_lon(self, response: Any, **kwargs: Any) -> Any:
        item = response.meta["item"]
        extract_google_position(item, response)
        yield item
