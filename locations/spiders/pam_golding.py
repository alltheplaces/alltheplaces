from collections import Counter
from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.country_utils import CountryUtils
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PamGoldingSpider(JSONBlobSpider):
    name = "pam_golding"
    item_attributes = {
        "brand": "Pam Golding Properties",
        "brand_wikidata": "Q65051429",
    }
    skip_auto_cc_domain = True
    country_utils = CountryUtils()

    async def start(self) -> Any:
        yield JsonRequest("https://webapi.pamgolding.co.za/api/agentsoffices/search-offices", data={})

    def extract_json(self, response: Response) -> list[dict]:
        offices = [
            office for country in response.json() for section in country["sections"] for office in section["offices"]
        ]
        self.unique_phones = {k for k, v in Counter(o.get("number") for o in offices).items() if v == 1}
        self.unique_emails = {k for k, v in Counter(o.get("email") for o in offices).items() if v == 1}
        return offices

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = item.pop("name")
        item["website"] = "https://www.pamgolding.co.za" + location["url"]
        item["addr_full"] = location.get("address")
        item["lat"] = location["geoPoint"]["lat"]
        item["lon"] = location["geoPoint"]["lon"]
        item["state"] = location["location"]["provinceName"]
        item["country"] = self.country_utils.to_iso_alpha2_country_code(location["location"]["countryName"])
        item["phone"] = location["number"] if location.get("number") in self.unique_phones else None
        item["email"] = location["email"] if location.get("email") in self.unique_emails else None
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
