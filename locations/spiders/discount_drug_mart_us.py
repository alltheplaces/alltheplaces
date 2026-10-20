import html
import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# The pharmacy at nearly every store closes for the same lunch break, which
# is called out separately in the "pharmacy_hours" free text rather than
# being reflected in the structured open/close times.
PHARMACY_LUNCH_BREAK = ("13:30", "14:00")


class DiscountDrugMartUSSpider(Spider):
    name = "discount_drug_mart_us"
    item_attributes = {"brand": "Discount Drug Mart", "brand_wikidata": "Q5281733", "name": "Discount Drug Mart"}
    start_urls = ["https://discount-drugmart.com/our-store/store-locator/"]

    def parse(self, response):
        stores = json.loads(re.search(r"var stores = (\[.*?\]);", response.text).group(1))

        for store in stores:
            if store.get("active") != "1":
                continue
            if store["store"] == "901":
                # Store 901 is the corporate head office, not a retail pharmacy.
                continue

            item = DictParser.parse(store)
            item["ref"] = store["store"]
            item["website"] = response.url
            if store.get("fax"):
                item["extras"]["fax"] = store["fax"]

            item["opening_hours"] = OpeningHours()
            if store_hours := store.get("store_hours"):
                item["opening_hours"].add_ranges_from_string(store_hours)
            if pharmacy_hours := self.parse_pharmacy_hours(store.get("pharmacy_hours")):
                item["extras"]["opening_hours:pharmacy"] = pharmacy_hours.as_opening_hours()

            apply_category(Categories.PHARMACY, item)

            yield item

    def parse_pharmacy_hours(self, hours_string: str) -> OpeningHours | None:
        if not hours_string or hours_string.strip().upper() == "N/A":
            return None

        hours_string = html.unescape(hours_string).replace("*", "")
        has_lunch_break = "closed for lunch" in hours_string.lower()
        main_hours = hours_string.split(" - Closed for lunch")[0].strip()

        oh = OpeningHours()
        for days, open_time, close_time in OpeningHours.extract_hours_from_string(main_hours):
            for day in days:
                if has_lunch_break and open_time < PHARMACY_LUNCH_BREAK[0] < close_time:
                    oh.add_range(day, open_time, PHARMACY_LUNCH_BREAK[0])
                    oh.add_range(day, PHARMACY_LUNCH_BREAK[1], close_time)
                else:
                    oh.add_range(day, open_time, close_time)
        return oh
