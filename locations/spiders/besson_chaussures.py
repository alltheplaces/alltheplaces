import re
from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

LOCATOR_DATA = "window.retailerLocatorData = "
CUSTOMER_SERVICE_PHONE = "+33806800004"
# The site numbers days from Sunday.
DAYS_BY_NUMBER = {"0": "Su", "1": "Mo", "2": "Tu", "3": "We", "4": "Th", "5": "Fr", "6": "Sa"}


class BessonChaussuresSpider(JSONBlobSpider):
    name = "besson_chaussures"
    item_attributes = {"brand": "Besson Chaussures", "brand_wikidata": "Q2899930", "name": "Besson Chaussures"}
    start_urls = ["https://www.besson-shoes.com/fr/retailer/retailer"]
    # DataDome blocks plain requests.
    requires_proxy = "FR"
    # Zyte gets a website ban when the project User-Agent is forwarded, so let it set its own.
    custom_settings = {"ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"]}
    # The only email is a customer service address shared by the Spanish stores.
    drop_attributes = {"email"}

    def extract_json(self, response: TextResponse) -> list[dict]:
        # All stores are embedded in the page as long as the map does not load them on demand.
        if re.search(r'"lazyLoading":\s*(1|true)', response.text):
            self.logger.error("Store finder now lazy-loads stores, the embedded list may be partial")
        script = response.xpath(f'//script[contains(text(), "{LOCATOR_DATA}")]/text()').get("")
        return chompjs.parse_js_object(script.split(LOCATOR_DATA, 1)[-1])["retailers"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("code")
        item["branch"] = re.sub(r"^BESSON (CHAUSSURES|CALZADOS)\s+", "", item.pop("name", None) or "", flags=re.I)
        item["street_address"] = merge_address_lines([feature.get("street"), feature.get("street_bis")])
        item.pop("street", None)
        item["website"] = feature.get("url_key")
        if feature.get("phone_number") == CUSTOMER_SERVICE_PHONE:
            item.pop("phone", None)

        # NSI only matches the French stores, so set the category for all of them here.
        apply_category(Categories.SHOP_SHOES, item)
        if "second-life" in (feature.get("keyword") or ""):
            apply_yes_no("second_hand", item, True)

        try:
            oh = OpeningHours()
            for slots in feature.get("schedule_data") or []:
                for slot in slots or []:
                    if slot.get("exceptional_date"):
                        continue
                    if day := DAYS_BY_NUMBER.get(str(slot.get("day_number"))):
                        oh.add_range(day, slot.get("start_time"), slot.get("end_time"))
            if oh:
                item["opening_hours"] = oh
        except ValueError:
            # Publish no hours rather than partial ones when a time is malformed.
            self.logger.warning(f"Unparseable opening hours for store {item['ref']}")

        yield item
