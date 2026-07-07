from typing import Any, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ScoutsSpider(JSONBlobSpider):
    name = "scouts"
    item_attributes = {
        "brand": "The Scout Association",
        "brand_wikidata": "Q849740",
    }
    start_urls = [
        "https://tsa-homesite-groupfinder-prd-weba-hwfvbvb4c3h7c6a2.uksouth-01.azurewebsites.net/GroupFinder?page=1&pageSize=500&location=london"
    ]
    locations_key = "Data"
    skip_auto_cc_domain = True

    def parse(self, response: TextResponse) -> Any:
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features)
        if not response.json()["PagingData"]["LastPage"]:
            yield JsonRequest(
                url=response.urljoin(response.json()["PagingData"]["nextPage"]),
                callback=self.parse,
            )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if item.get("postcode") is not None and item["postcode"].lower() == "null":
            item.pop("postcode")
        item["website"] = f"https://www.scouts.org.uk/groups/{feature['Id']}?slug={feature['Slug']}"
        yield item
