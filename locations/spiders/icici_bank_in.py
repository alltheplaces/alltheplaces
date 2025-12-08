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

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in json.loads(response.text)["branch"]:
            item = DictParser.parse(branch)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = branch["branchName"]
            item["name"] = None
            item["ref"] = branch["ifsc"]
            item["postcode"] = branch["pincode"]
            item["website"] = f'https://www.icicibank.com{branch["knowMoreUrl"]}'
            try:
                if hours := branch.get("mondayToSaturdayBranchWorking", ""):
                    if m := re.search(
                        r"(\d+:\d+(?:AM|PM))-(\d+:\d+(?:AM|PM))",
                        hours.replace(".", ":").replace(" ", ""),
                    ):
                        item["opening_hours"] = OpeningHours()
                        item["opening_hours"].add_days_range(DAYS[0:6], m.group(1), m.group(2), "%I:%M%p")
            except Exception as e:
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
                self.logger.warning(f"Failed to parse hours for {item['ref']}, {e}")

            apply_category(Categories.BANK, item)

            yield item

        for atm in json.loads(response.text)["atm"]:
            item = DictParser.parse(atm)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").replace("ICICI Bank ATM in ", "").strip()
            item["ref"] = atm["siteId"]
            item["postcode"] = atm["pinCode"]
            item["website"] = f'https://www.icicibank.com{atm["knowMoreUrl"]}'.replace("/en/", "/")

            apply_category(Categories.ATM, item)
            if "N/A" in item.get("lat"):
                item["lat"] = None
                item["lon"] = None
            yield item
