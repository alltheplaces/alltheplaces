import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

BRANDS = {
    "丸善": "Q1906012",
    "ジュンク堂書店": "Q3190093",
    "淳久堂書店": "Q3190093",
}


class MaruzenJunkudoSpider(JSONBlobSpider):
    name = "maruzen_junkudo"
    item_attributes = {"operator": "丸善ジュンク堂書店", "operator_wikidata": "Q107411688"}
    start_urls = ["https://api-shopify-listLocations-ttmpxhtqra-an.a.run.app"]
    locations_key = ["locations", "edges"]

    def pre_process_data(self, feature: dict) -> None:
        node = feature.pop("node")
        feature.update(node)
        feature.update({field["node"]["key"]: field["node"]["value"] for field in node["metafields"]["edges"]})

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        brand = feature["store_name"]
        if brand in ("M.LEAGUE OFFICIAL SHOP", "Personal Lounge"):
            return
        item["ref"] = feature["code"]
        item["brand"] = brand
        item["brand_wikidata"] = BRANDS.get(brand)
        item["branch"] = feature["name"].removeprefix(brand).strip() or None
        item["name"] = brand
        item["street_address"] = merge_address_lines([feature["address"]["address1"], feature["address"]["address2"]])
        item["phone"] = feature["address"]["phone"]
        item["website"] = feature["detail_url"]
        item["extras"]["contact:twitter"] = feature.get("xtwitter")
        item["extras"]["contact:instagram"] = feature.get("instagram")

        if "無休" in feature["regular_holiday"] and (
            hours := re.fullmatch(r"(\d{1,2}:\d{2})~(\d{1,2}:\d{2})", feature["business_hours"].strip())
        ):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, *hours.groups())

        apply_category(Categories.SHOP_BOOKS, item)
        yield item
