from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MoltonBrownSpider(JSONBlobSpider):
    name = "molton_brown"
    item_attributes = {"brand": "Molton Brown", "brand_wikidata": "Q17100584"}
    locations_key = ["stores"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.moltonbrown.co.uk",
            "referer": "https://www.moltonbrown.co.uk/",
        },
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 10,
    }

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://api.moltonbrown.com/kaowebservices/v2/moltonbrown-gb/stores/?currentPage={page}",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(0)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        features = self.extract_json(response)
        if isinstance(features, dict):
            yield from self.parse_feature_dict(response, features) or []
        else:
            yield from self.parse_feature_array(response, features) or []
        if response.json()["pagination"]["totalPages"] > response.meta["page"]:
            if response.meta["page"] == 1:
                # page 2 gives a 400 error
                # page 6 also gives an error - there must be shops missing from these 2 pages It doesn't have the 2 stores in Greece for example.
                yield self.make_request(response.meta["page"] + 2)
            else:
                yield self.make_request(response.meta["page"] + 1)

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature["name"]
        if feature.get("displayName"):
            feature["name"] = feature["displayName"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if item.get("website"):
            item["website"] = "https://www.moltonbrown.co.uk/store/store-finder/" + item["website"].replace(" ", "-")
            # the link on the Molton Brown site includes a space
        if feature["storeType"] == "MBSTORES":
            yield item
