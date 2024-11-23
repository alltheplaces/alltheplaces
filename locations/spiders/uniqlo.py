from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UniqloSpider(JSONBlobSpider):
    name = "uniqlo"
    item_attributes = {"brand": "Uniqlo", "brand_wikidata": "Q26070"}
    locations_key = ["result", "stores"]
    offset = 0

    def start_requests(self):
        for country in [
            "jp",
            "uk",
            "fr",
            "de",
            "es",
            "it",
            "dk",
            "se",
            "be",
            "nl",
            "eu-lu",
            "eu-pl",
        ]:
            yield from self.request_page(country, 0)

    def request_page(self, country, offset):
        yield JsonRequest(
            url=f"https://map.uniqlo.com/{country}/api/storelocator/v1/en/stores?limit=100&RESET=true&offset={offset}&r=storelocator",
            meta={
                "country": country,
                "offset": offset,
            },
        )

    def parse(self, response):
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        pagination = response.json()["result"]["pagination"]
        if pagination["total"] > pagination["offset"] + pagination["count"]:
            offset = response.meta["offset"] + 100
            country = response.meta["country"]
            yield from self.request_page(country, offset)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        oh = OpeningHours()
        for day in DAYS:
            if day == "Su":
                oh.add_range(day, feature["weHolOpenAt"], feature["weHolCloseAt"])
            else:
                oh.add_range(day, feature["wdOpenAt"], feature["wdCloseAt"])
        item["opening_hours"] = oh
        item["website"] = f'https://map.uniqlo.com/{response.meta["country"]}/en/detail/{feature["id"]}'

        yield item
