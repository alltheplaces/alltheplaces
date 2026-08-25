from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class NeimanMarcusUSSpider(JSONBlobSpider):
    name = "neiman_marcus_us"
    item_attributes = {"brand": "Neiman Marcus", "brand_wikidata": "Q743497"}
    start_urls = ["https://stores.neimanmarcus.com/info/min/allStoresAddr_nm.min.json"]

    def extract_json(self, response: Response) -> list[dict]:
        return [feature for state in response.json().values() for feature in state]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([feature.get("addressLine1"), feature.get("addressLine2")])
        item["phone"] = (feature.get("phoneNumbers") or [None])[0]
        item["image"] = feature.get("mainImageUrl")
        item["opening_hours"] = OpeningHours()
        for day in feature.get("workingHours") or []:
            for hours in day.get("hours") or []:
                if hours.strip().upper() == "CLOSED":
                    item["opening_hours"].set_closed(day["label"])
                else:
                    item["opening_hours"].add_ranges_from_string(f"{day['label']}: {hours}")
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
