import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NO, DAYS_NO, OpeningHours, sanitise_day
from locations.items import Feature


class FargerikeNOSpider(Spider):
    """Spider for Fargerike paint stores in Norway. Closes #7697."""

    name = "fargerike_no"
    item_attributes = {
        "brand": "Fargerike",
        "brand_wikidata": "Q56487613",
    }
    start_urls = ["https://www.fargerike.no/fargehandel/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The store data is embedded as a ReactDOM.hydrate prop in a script tag:
        # ReactDOM.hydrate(React.createElement(Components.FindStore, {"initialData":[...]}))
        script_text = response.xpath("//script[contains(., 'initialData')]/text()").get("")

        m = re.search(r'"initialData"\s*:\s*(\[)', script_text)
        if not m:
            self.logger.error("Could not find initialData in page")
            return

        start = m.start(1)
        depth = 0
        end = start
        for i in range(start, len(script_text)):
            if script_text[i] == "[":
                depth += 1
            elif script_text[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        stores = json.loads(script_text[start:end])

        for store in stores:
            oh = self._parse_opening_hours(store.get("openingHours", []))

            # Derive branch name: prefer the "name" field, otherwise use the local part of the email
            name_field = store.get("name") or ""
            if name_field.lower().startswith("fargerike "):
                branch = name_field[len("fargerike ") :].strip()
            elif name_field:
                branch = name_field
            else:
                email = store.get("mailAddressStore") or ""
                branch = email.split("@")[0] if email else None

            ref = store.get("lindbakStoreId") or store.get("farveringenId")
            item = Feature()
            item["ref"] = ref
            item["branch"] = branch
            item["phone"] = store.get("phoneNumberStore") or None
            item["email"] = store.get("mailAddressStore") or None
            item["street_address"] = store.get("address")
            item["postcode"] = store.get("postCode")
            item["city"] = store.get("postDistrict")
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["country"] = "NO"
            item["opening_hours"] = oh
            item["website"] = "https://www.fargerike.no" + store["externalUrl"] if store.get("externalUrl") else None
            apply_category(Categories.SHOP_PAINT, item)
            yield item

    @staticmethod
    def _parse_opening_hours(hours_list: list) -> OpeningHours:
        oh = OpeningHours()
        for entry in hours_list:
            day_no = entry.get("day", "")
            time_str = entry.get("time", "")
            day_en = sanitise_day(day_no, DAYS_NO)
            if not day_en:
                continue
            if time_str.lower() in CLOSED_NO:
                oh.set_closed(day_en)
            else:
                parts = time_str.split(" - ")
                if len(parts) == 2:
                    oh.add_range(day_en, parts[0].strip(), parts[1].strip())
        return oh
