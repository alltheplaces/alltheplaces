import json
from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy.http import JsonRequest, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import FIREFOX_LATEST


class IciParisXlSpider(JSONBlobSpider, PlaywrightSpider):
    name = "ici_paris_xl"
    item_attributes = {"brand": "ICI PARIS XL", "brand_wikidata": "Q769749"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": FIREFOX_LATEST}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country in ["be", "nl", "lu"]:
            yield JsonRequest(
                f"https://api.iciparisxl.{country}/api/v2/ici{country}2/stores?pageSize=10000&currentPage=0"
            )

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        print(response.text)
        json_data = json.loads(response.xpath("//pre//text()").get())["stores"]
        return json_data

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        item["branch"] = feature.get("displayName")
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])
        item["addr_full"] = feature.get("formattedAddress")
        item["website"] = item["ref"] = urljoin(f'https://www.iciparisxl.{item["country"].lower()}', feature.get("url"))
        try:
            item["opening_hours"] = OpeningHours()
            for rule in feature.get("openingHours", {}).get("weekDayOpeningList", []):
                if day := sanitise_day(rule.get("shortenedWeekDay")):
                    if rule.get("closed"):
                        item["opening_hours"].set_closed(day)
                    else:
                        item["opening_hours"].add_range(
                            day,
                            rule.get("openingTime", {}).get("formattedHour"),
                            rule.get("closingTime", {}).get("formattedHour"),
                            "%I:%M %p",
                        )
        except:
            pass
        apply_category(Categories.SHOP_PERFUMERY, item)
        yield item
