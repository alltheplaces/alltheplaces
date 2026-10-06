import json
import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

STORE_URL = "https://www.target.com/sl/store/{}"


class TargetUSSpider(SitemapSpider):
    name = "target_us"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q1046951"}
    allowed_domains = ["target.com"]
    sitemap_urls = ["https://www.target.com/sitemap_stores-index.xml.gz"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            if entry["loc"].endswith(".xml") or entry["loc"].endswith(".xml.gz"):
                yield entry
            elif match := re.search(r"/(\d+)$", entry["loc"]):
                entry["loc"] = STORE_URL.format(match.group(1))
                yield entry

    def extract_store(self, html: str) -> dict[str, Any] | None:
        if not (match := re.search(r'\\"store\\":\{\\"store\\":\{', html)):
            return None

        # Slice to the end of the script tag and unescape quotes/slashes
        payload = html[match.end() - 1 : html.find("</script>", match.end())]
        unescaped = payload.replace('\\"', '"').replace("\\\\", "\\")

        try:
            store_obj, _ = json.JSONDecoder().raw_decode(unescaped)
            return store_obj
        except json.JSONDecodeError:
            return None

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (store := self.extract_store(response.text)):
            return
        if store.get("is_test_location"):
            return

        store.update(store.pop("mailing_address", {}))
        store.update(store.pop("geographic_specifications", {}))
        item = DictParser.parse(store)
        item["name"] = None
        item["branch"] = store.get("location_name")
        item["website"] = STORE_URL.format(store["store_id"])

        for contact_info in store.get("contact_information", []):
            if contact_info.get("telephone_type") == "VOICE":
                item["phone"] = contact_info.get("telephone_number")
            elif contact_info.get("telephone_type") == "FAX":
                item["extras"]["fax"] = contact_info.get("telephone_number")

        if geofence := store.get("geofence"):
            if radius := geofence.get("radius"):
                item["extras"]["geofence:radius"] = radius

        if drive_up := store.get("drive_up"):
            item["extras"]["drive_through"] = "yes"
            if lat := drive_up.get("latitude"):
                item["extras"]["drive_up:lat"] = lat
            if lon := drive_up.get("longitude"):
                item["extras"]["drive_up:lon"] = lon
            if radius := drive_up.get("radius"):
                item["extras"]["drive_up:radius"] = radius

        opening_hours_info = store.get("rolling_operating_hours", {}).get("main_hours", {}).get("days") or []
        item["opening_hours"] = self.parse_opening_hours(opening_hours_info)

        if store.get("physical_specifications", {}).get("format") == "SuperTarget":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules[:7]:
            day = rule.get("day_name")
            if rule.get("is_open") is False:
                oh.set_closed(day)
                continue
            for shift in rule.get("hours", []):
                oh.add_range(day, shift["begin_time"], shift["end_time"], "%H:%M:%S")
        return oh
