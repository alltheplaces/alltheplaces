from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MarcusTheatresSpider(JSONBlobSpider):
    name = "marcus_theatres"
    item_attributes = {"brand": "Marcus Cinema", "brand_wikidata": "Q64083352"}
    api_url = "https://api-injin.marcustheatres.com"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"{self.api_url}/user/v2/token",
            method="POST",
            headers={"Authorization": "Basic d2Vic2l0ZUBpbmppbi5jb206MEhDcntmIXtzXjA4bkpXLjdyIzBxa2p3"},
            callback=self.parse_access_token,
        )

    def parse_access_token(self, response: Response) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url=f"{self.api_url}/cms/v2/cinemas",
            headers={"Authorization": f"Bearer {response.json()['accessToken']}"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["cinemaid"]
        item["branch"] = item.pop("name")
        item["street_address"] = feature["address1"]
        item["city"] = feature["city"][0]
        item["state"] = feature["states"][0]
        item["website"] = f"https://www.marcustheatres.com/theatre-locations/{feature['urlSafeName']}"
        apply_category(Categories.CINEMA, item)
        yield item
