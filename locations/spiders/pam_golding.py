from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PamGoldingSpider(JSONBlobSpider):
    name = "pam_golding"
    item_attributes = {"brand": "Pam Golding Properties", "brand_wikidata": "Q65051429"}
    skip_auto_cc_domain = True

    async def start(self) -> Any:
        yield JsonRequest("https://webapi.pamgolding.co.za/api/agentsoffices/search-offices", data={})

    def extract_json(self, response: Response) -> list[dict]:
        return [
            office for country in response.json() for section in country["sections"] for office in section["offices"]
        ]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = item.pop("name")
        item["website"] = "https://www.pamgolding.co.za" + location["url"]
        item["addr_full"] = location.get("address")
        item["lat"] = location["geoPoint"]["lat"]
        item["lon"] = location["geoPoint"]["lon"]
        item["state"] = location["location"]["provinceName"]
        item["country"] = location["location"]["countryName"]
        item["phone"] = location["number"]
        item["email"] = location["email"]
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
