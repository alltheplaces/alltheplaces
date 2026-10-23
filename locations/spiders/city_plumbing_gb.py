from typing import Iterable

import re
import chompjs

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_FULL
from locations.pipelines.address_clean_up import merge_address_lines
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

class CityPlumbingGBSpider(JSONBlobSpider):
    name = "city_plumbing_gb"
    item_attributes = {"name": "City Plumbing Supplies", "brand": "City Plumbing Supplies", "brand_wikidata": "Q105089893"}
    start_urls = ["https://www.cityplumbing.co.uk/branch-locator"]

    def extract_json(self, response: Response) -> list[dict]:
        searchstr = '"allBranches":'
        script = response.xpath(f"//script[contains(text(), '{searchstr}')]/text()").get()
        start = script.find(searchstr) + len(searchstr)
        locations = chompjs.parse_js_object(script[start:])
        return locations

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("code")
        item["branch"] = item.pop("name").removesuffix("CPS").strip()
        item["website"] = "https://www.cityplumbing.co.uk/branch-locator/" + item["ref"] + "/" + item["branch"].lower().replace(" ","-")
        item["street_address"] = merge_address_lines ([feature.get("address")["line2"],feature.get("address")["line3"]])
        if feature.get("branchSchedule"):
            item["opening_hours"] = OpeningHours()
            for day in feature["branchSchedule"]:
                item["opening_hours"].add_range(day["dayOfWeek"],day["openingTime"],day["closingTime"])
        apply_category(Categories.TRADE_PLUMBING, item)
        yield item
