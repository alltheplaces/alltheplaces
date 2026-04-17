import json
from typing import Iterable

from scrapy.http import Response, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class ReiUSSpider(JSONBlobSpider, PlaywrightSpider):
    name = "rei_us"
    item_attributes = {
        "brand": "REI",
        "brand_wikidata": "Q3414933",
        "country": "US",
    }

    start_urls = ["https://www.rei.com/stores/map"]
    requires_proxy = True

    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "USER_AGENT": BROWSER_DEFAULT,
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        raw_data = response.xpath('//script[@id="modelData"]/text()').get()
        if not raw_data:
            return []
        data = json.loads(raw_data)
        raw_stores = data.get("pageData", {}).get("allStores", {}).get("storeLocatorDataQueryModelList", [])
        return [s.get("storeDataModel") for s in raw_stores if s.get("storeDataModel")]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature.get("storeNumber"))

        if url_path := feature.get("storePageUrl"):
            item["website"] = f"https://www.rei.com/{url_path.lstrip('/')}"

        if hours_list := feature.get("storeHours"):
            item["opening_hours"] = self.parse_opening_hours(hours_list)

        yield item

    def parse_opening_hours(self, hours_list: list) -> str:
        oh = OpeningHours()
        for h in hours_list:
            day_part = h.get("days")
            open_t = h.get("openAt")
            close_t = h.get("closeAt")
            if day_part and open_t and close_t:
                oh.add_ranges_from_string(f"{day_part} {open_t} - {close_t}")
        return oh
