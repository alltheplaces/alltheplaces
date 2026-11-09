from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class CityPlumbingGBSpider(JSONBlobSpider):
    name = "city_plumbing_gb"
    BRAND_MAPPING = {
        "CPS": {"brand": "City Plumbing", "name": "City Plumging Supplies", "brand_wikidata": "Q105089893"},
        "PTS": {"brand": "Plumbing Trade Supplies", "name": "Plumbing Trade Supplies", "brand_wikidata": "Q141831571"},
    }
    start_urls = ["https://www.cityplumbing.co.uk/branch-locator"]

    def extract_json(self, response: Response) -> list[dict]:
        searchstr = '"allBranches":'
        script = response.xpath(f"//script[contains(text(), '{searchstr}')]/text()").get()
        if script is None:
            return []
        start = script.find(searchstr) + len(searchstr)
        locations = chompjs.parse_js_object(script[start:])
        return locations

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("code")
        if item["name"].endswith("PTS"):
            item["branch"] = item.pop("name").removesuffix("PTS").strip()
            item.update(self.BRAND_MAPPING.get("PTS"))
        else:
            item["branch"] = item.pop("name").removesuffix("CPS").strip()
            item.update(self.BRAND_MAPPING.get("CPS"))
        item["website"] = (
            "https://www.cityplumbing.co.uk/branch-locator/"
            + item["ref"]
            + "/"
            + item["branch"].lower().replace(" ", "-")
        )
        address = feature.get("address") or {}
        item["street_address"] = merge_address_lines([address.get("line2"), address.get("line3")])
        if feature.get("branchSchedule"):
            item["opening_hours"] = OpeningHours()
            for day in feature["branchSchedule"]:
                item["opening_hours"].add_range(day["dayOfWeek"], day["openingTime"], day["closingTime"])
        apply_category(Categories.TRADE_PLUMBING, item)
        apply_category(Categories.SHOP_TRADE, item)
        yield item
