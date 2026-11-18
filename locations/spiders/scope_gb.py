from itertools import chain
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Request, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class ScopeGBSpider(JSONBlobSpider):
    name = "scope_gb"
    item_attributes = {"brand": "Scope", "brand_wikidata": "Q7434435"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.scope.org.uk/api/shops/loadmore?page={page}&pagepath=/charity-shops/shop-directory&location=&type=Show%20all&dropBanks=true",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(0)

    def extract_json(self, response: TextResponse) -> list[dict]:
        return list(chain.from_iterable(response.json()["results"]))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # use extract_json so the flattened list is what gets parsed
        yield from self.parse_feature_array(response, self.extract_json(response))

        page = response.meta["page"]
        if (page + 1) * 6 < response.json()["matchCount"]:
            yield self.make_request(page + 1)

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["title"]
        for entry in feature.pop("items", []):
            icon = entry["icon"]
            if "clock" in icon:
                feature["hours"] = entry["label"]
            elif "location" in icon:
                feature["address"] = entry["label"].split(" | ")[0]
            elif "phone" in icon:
                feature["phone"] = entry["label"]

    def post_process_item(self, item, response, location):
        item["name"] = location["title"]
        item["addr_full"] = clean_address(location.get("address"))
        item["phone"] = location.get("phone")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location.get("hours"))

        if "bank" in location["subtitle"].lower():
            apply_category(
                {"amenity": "recycling", "recycling_type": "container", "recycling:clothes": "yes"},
                item,
            )
        else:
            apply_category(Categories.SHOP_CHARITY, item)

        yield item
