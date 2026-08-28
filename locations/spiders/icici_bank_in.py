import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class IciciBankINSpider(Spider):
    name = "icici_bank_in"
    item_attributes = {"brand": "ICICI Bank", "brand_wikidata": "Q1653258"}
    start_urls = ["https://maps.icicibank.com/content/icicibank/in/en.microsite.json"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    @staticmethod
    def parse_time_range(hours: str) -> tuple[str, str] | None:
        if m := re.search(r"(\d+:\d+(?:AM|PM))-(\d+:\d+(?:AM|PM))", hours.replace(".", ":").replace(" ", "")):
            return m.group(1), m.group(2)
        return None

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in json.loads(response.text)["branch"]:
            item = DictParser.parse(branch)
            item["street_address"] = item.pop("addr_full", None)
            item["branch"] = branch.get("branchName")
            item["name"] = None
            item["ref"] = branch.get("ifsc")
            item["postcode"] = branch.get("pincode")
            if url := branch.get("knowMoreUrl"):
                item["website"] = f"https://www.icicibank.com{url}"
            try:
                oh = OpeningHours()
                if weekday := self.parse_time_range(branch.get("mondayToFridayWorkingHrs") or ""):
                    oh.add_days_range(DAYS[0:5], *weekday, "%I:%M%p")
                if saturday := self.parse_time_range(branch.get("saturdayWorkingHrs") or ""):
                    oh.add_range("Sa", *saturday, "%I:%M%p")
                if oh.day_hours:
                    item["opening_hours"] = oh
            except Exception as e:
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
                self.logger.warning(f"Failed to parse hours for {item['ref']}, {e}")

            apply_category(Categories.BANK, item)

            yield item

        for atm in json.loads(response.text)["atm"]:
            item = DictParser.parse(atm)
            item["street_address"] = item.pop("addr_full", None)
            if name := item.pop("name", None):
                item["branch"] = name.replace("ICICI Bank ATM in ", "").strip()
            item["ref"] = atm.get("siteId")
            item["postcode"] = atm.get("pinCode")
            if url := atm.get("knowMoreUrl"):
                item["website"] = f"https://www.icicibank.com{url}".replace("/en/", "/")
            if atm.get("atm") == "24X7":
                item["opening_hours"] = "24/7"

            apply_category(Categories.ATM, item)
            if item.get("lat") and "N/A" in item["lat"]:
                item["lat"] = None
                item["lon"] = None
            yield item
