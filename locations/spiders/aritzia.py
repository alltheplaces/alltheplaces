import json
import re
from typing import Iterable

from scrapy.http import Response, TextResponse

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

# Aritzia's own boutique concept stores ("Wilfred", "TNA", "Babaton") for its
# in-house clothing labels appear in the same store locator feed but are a
# different retail identity to "Aritzia" itself, so they are excluded here.
NON_ARITZIA_STORE_ID_PREFIXES = ("wilfred-", "tna-", "babaton-")

COUNTRY_CODES = {
    "United States": "US",
    "Canada": "CA",
    "CA": "CA",
}


class AritziaSpider(JSONBlobSpider, CamoufoxSpider):
    name = "aritzia"
    item_attributes = {"brand": "Aritzia", "brand_wikidata": "Q4791147", "name": "Aritzia"}
    start_urls = ["https://www.aritzia.com/us/en/store-locator"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    # These fields carry per-locale sub-dicts (e.g. "fr") that are needed
    # as-is, so they are excluded from the generic "en" value flattening.
    multi_locale_fields = {"storeDetailsTitle", "storeHours"}

    def extract_json(self, response: TextResponse) -> list[dict]:
        blob = response.xpath('//script[@id="mobify-data"]/text()').get()
        return json.loads(blob)["__PRELOADED_STATE__"]["pageProps"]["results"]

    def pre_process_data(self, feature: dict) -> None:
        # Flatten the Contentful-style {"en": value} field wrappers used
        # throughout this feed into plain scalar values.
        for key, value in list(feature["fields"].items()):
            if key in self.multi_locale_fields:
                continue
            feature["fields"][key] = value.get("en") if isinstance(value, dict) else value
        feature.update(feature.pop("fields"))

    def parse_feature_array(self, response: Response, features: list[dict]) -> Iterable[Feature]:
        for feature in features:
            self.pre_process_data(feature)

            store_id = feature.get("storeId") or ""
            if store_id.startswith(NON_ARITZIA_STORE_ID_PREFIXES):
                continue

            title_fr = (feature.get("storeDetailsTitle") or {}).get("fr") or ""
            if "venir tr" in title_fr.lower():
                # Store has not opened yet ("coming soon").
                continue

            item = Feature()
            item["ref"] = store_id
            item["branch"] = feature.get("storeName", "").strip()
            item["street_address"] = merge_address_lines(
                [feature.get("storeAddressLine1"), feature.get("storeAddressLine2")]
            )
            item["city"] = feature.get("city")
            item["state"] = feature.get("stateprovinceAbbreviation")
            item["postcode"] = feature.get("postalCode")
            item["country"] = COUNTRY_CODES.get(feature.get("country"))
            item["phone"] = feature.get("phoneNumber")
            item["lat"] = feature.get("latitude")
            item["lon"] = feature.get("longitude")

            # The source's own "route" field is unreliable (seen with a
            # missing leading slash, and with the StoreID duplicated), so
            # the URL is instead built from the canonical store_id.
            locale = "us" if item["country"] == "US" else "ca"
            item["website"] = f"https://www.aritzia.com/{locale}/en/store?StoreID={store_id}"

            item["opening_hours"] = self.parse_hours((feature.get("storeHours") or {}).get("en") or [])

            apply_category(Categories.SHOP_CLOTHES, item)
            apply_category({"clothes": "women"}, item)

            yield item

    @staticmethod
    def parse_hours(day_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day_hour in day_hours:
            day = day_hour.get("key")
            value = (day_hour.get("value") or "").strip()
            if not value or value.upper() == "CLOSED":
                oh.add_range(day, "closed", "closed")
                continue
            if match := re.match(r"^(.+?)\s*-\s*(.+)$", value):
                oh.add_range(day, match.group(1), match.group(2), time_format="%I:%M %p")
        return oh
