from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

COLUMNS = {
    "1": "name",
    "4": "location",
    "5": "email",
    "6": "phone",
    "8": "address",
    "19": "state",
    "27": "website",
    "56": "ref",
}


class KidStrongUSSpider(JSONBlobSpider):
    name = "kid_strong_us"
    item_attributes = {"brand": "KidStrong", "brand_wikidata": "Q125705878"}
    start_urls = ["https://api.hubapi.com/hubdb/api/v2/tables/5311378/rows?portalId=20820444"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def extract_json(self, response: Response) -> list[dict]:
        features = []
        for row in response.json()["objects"]:
            values = row.get("values") or {}
            if values.get("57") != "yes":  # location_active
                continue
            features.append({name: values.get(column) for column, name in COLUMNS.items()})
        return features

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("KidStrong ")
        item["website"] = f'https://{feature["website"]}' if feature.get("website") else None
        apply_category(Categories.GYM, item)
        yield item
