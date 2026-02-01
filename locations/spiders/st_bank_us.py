import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class StBankUSSpider(Spider):
    name = "st_bank_us"
    item_attributes = {"brand": "S&T Bank", "brand_wikidata": "Q122170137"}
    allowed_domains = ["stbank.com"]
    start_urls = ["https://www.stbank.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in data["props"]["pageProps"]["data"]["locations"]["nodes"]:
            yield self.parse_location(location)

    def parse_location(self, location) -> Feature:
        loc_data = location.pop("location")
        location |= loc_data | loc_data.pop("address")

        item = DictParser.parse(location)
        item["ref"] = location["title"]
        item["addr_full"] = item.pop("street_address")
        item["country"] = "US"

        location_type = location.get("typeSelect", "")
        if location_type == "ATM":
            apply_category(Categories.ATM, item)
        else:
            item["branch"] = item.pop("name")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "ATM" in location_type)

        hours_data = location.get("hours") or []
        apply_yes_no(
            Extras.DRIVE_THROUGH,
            item,
            any("drive" in h.get("entry", {}).get("text", {}).get("textEntry", "").lower() for h in hours_data),
        )

        try:
            item["opening_hours"] = self.parse_opening_hours(hours_data)
        except:
            self.logger.error(f"Failed to parse opening hours for {item['ref']}")
        return item

    def parse_opening_hours(self, hours_data: list | None) -> OpeningHours:
        oh = OpeningHours()
        for hours_entry in hours_data or []:
            entry = hours_entry.get("entry", {})
            if entry.get("text", {}).get("textEntry", "").lower() not in ["lobby", ""]:
                continue
            for day_select in entry.get("daySelect", []):
                if day_select.get("storeOpen", True):
                    oh.add_days_range(
                        day_select.get("days", []), day_select["startTime"], day_select["endTime"], "%I:%M %p"
                    )
        return oh
