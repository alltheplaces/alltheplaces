
from scrapy.http import JsonRequest

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
        print(pagination)
        if pagination["total"] > pagination["offset"] + pagination["count"]:
            offset = response.meta["offset"] + 100
            country = response.meta["country"]
            yield from self.request_page(country, offset)
