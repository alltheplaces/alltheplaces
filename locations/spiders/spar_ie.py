import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES


class SparIESpider(Spider):
    name = "spar_ie"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    start_urls = ["https://www.spar.ie/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        match = re.search(
            r"stores\s*=\s*(\[.*?\]);",
            response.xpath("//script[contains(text(), 'stores')]/text()").get(),
            re.DOTALL,
        )

        for location in chompjs.parse_js_object(match.group(1)):
            if location.get("storeStatus") != "active":
                continue

            details = location.get("storeDetails", {})

            item = Feature()
            item["ref"] = location["storeId"]
            item["lat"] = details.get("Latitude")
            # few Longitude have space like "- 6.28455"
            item["lon"] = details.get("Longitude").replace(" ", "")
            item["phone"] = location.get("storePhone").replace("/", "").strip()
            item["postcode"] = details.get("PostCode")

            item["addr_full"] = merge_address_lines(
                [
                    details.get("AddressLine1"),
                    details.get("AddressLine2"),
                    details.get("AddressLine3"),
                ]
            )
            item["city"] = details.get("CountyName")

            raw_name = location.get("storeName", "Spar")
            item["name"] = "Spar Express" if "Express" in raw_name else "Spar"

            # SPAR and Spar both are present
            item["branch"] = re.sub(r"SPAR|Express", "", raw_name, flags=re.IGNORECASE).strip()

            if oh_raw := location.get("storeOpeningHours"):
                item["opening_hours"] = self.parse_hours(oh_raw)

            services = location.get("storeServices", [])
            apply_yes_no(Extras.ATM, item, "ATM" in services)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in services)
            apply_yes_no("sells:lottery", item, "Lotto" in services)

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item

    def parse_hours(self, oh_raw: str) -> OpeningHours:
        oh = OpeningHours()

        # for some location data is present like Mon-Fri: 07.00 - 21.00 and for other like Mon-Fri: 06:00 - 22:00
        clean_raw = oh_raw.replace("\\n", "\n").replace(".", ":")

        # to filter out cases like: "Mon-Fri: \nSat: \nSun:
        valid_opening_hours = re.findall(r"[\w-]+\s*:\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", clean_raw)
        filtered_string = "\n".join(valid_opening_hours)

        results = OpeningHours.extract_hours_from_string(
            ranges_string=filtered_string, days=DAYS_EN, delimiters=[":", "-", " - "]
        )

        for days, start_t, end_t in results:
            for day in days:
                oh.add_range(day, start_t, end_t)

        return oh
