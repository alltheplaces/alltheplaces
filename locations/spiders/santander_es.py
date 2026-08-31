import json
from typing import AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SantanderESSpider(JSONBlobSpider):
    """Spider for Banco Santander branches and ATMs in Spain.
    Closes #5778
    """

    name = "santander_es"
    item_attributes = {"brand": "Banco Santander", "brand_wikidata": "Q6496310"}
    locations_key = None  # response is a direct array

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("ES", 48):
            params = {
                "config": json.dumps({"coords": [lat, lon]}),
                "locale": "es_ES",
                "pageSize": "100",
                "globalSearch": "true",
            }
            yield JsonRequest(
                url=f"https://back-branchlocator.santander.com/v1/branch-locator/find/defaultView?{urlencode(params)}"
            )

    def extract_json(self, response: TextResponse):
        return response.json()

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("poiStatus") != "ACTIVE":
            return

        obj_type = feature.get("objectType", {}).get("code")
        if obj_type not in ("BRANCH", "ATM"):
            return  # skip CORRESPONSALES (correspondent banking agents)

        loc = feature.get("location", {})
        coords = loc.get("coordinates", [None, None])
        item["lon"] = coords[0]
        item["lat"] = coords[1]
        item["ref"] = feature.get("code")
        item["street_address"] = loc.get("address")
        item["postcode"] = loc.get("zipcode")
        item["city"] = loc.get("city")
        item["country"] = "ES"
        item.pop("name", None)  # name is just the branch number, not useful

        if obj_type == "BRANCH":
            apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.ATM, item)

        yield item
