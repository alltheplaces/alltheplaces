import json
from typing import Any

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class NandosUSSpider(StructuredDataSpider):
    name = "nandos_us"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    requires_proxy = True
    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DOWNLOAD_TIMEOUT": 30,
    }
    allowed_domains = ["nandosperiperi.com"]
    start_urls = ["https://www.nandosperiperi.com/all-locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Find the first JSON-LD ItemList and yield items or follow URLs.
        scripts = response.xpath("//script[@type='application/ld+json']/text()").getall()
        for script in scripts:
            try:
                data = json.loads(script)
            except Exception:
                continue

            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue

                types = obj.get("@type")
                if not types:
                    continue
                if (isinstance(types, list) and not any("itemlist" == t.lower() for t in types)) or (
                    isinstance(types, str) and "itemlist" != types.lower()
                ):
                    continue

                elements = obj.get("itemListElement")
                if not elements:
                    continue

                for element in elements:
                    if isinstance(element, dict):
                        item_obj = element.get("item") or element.get("mainEntity")
                        if isinstance(item_obj, dict):
                            item = LinkedDataParser.parse_ld(item_obj, time_format=self.time_format)
                            yield from self.post_process_item(item, response, item_obj)
                            continue
                        url = element.get("url") or element.get("@id")
                        if url:
                            yield response.follow(response.urljoin(url), callback=self.parse_sd)
                            continue

                    if isinstance(element, str) and element.startswith("http"):
                        yield response.follow(response.urljoin(element), callback=self.parse_sd)

                return  # Early exit after first valid ItemList
        # If no ItemList found, do nothing

    def extract_amenity_features(self, item, response: Response, ld_item):
        features = []
        for f in ld_item.get("amenityFeature") or []:
            if isinstance(f, dict):
                name = f.get("name")
                if name:
                    features.append(name)
            elif isinstance(f, str):
                features.append(f)

        apply_yes_no(
            Extras.INDOOR_SEATING, item, any("Dine In" in f or "Dine-In" in f or "Dine in" in f for f in features)
        )
        apply_yes_no(Extras.OUTDOOR_SEATING, item, any("Patio" in f or "Outdoor" in f for f in features))

    def post_process_item(self, item, response: Response, ld_item: dict, **kwargs: Any):
        if "name" in item:
            item["branch"] = item.pop("name")

        item["website"] = ld_item.get("mainEntityOfPage")

        # Ensure a unique ref for duplicates pipeline: prefer existing ref,
        # then linked-data @id or url, then website path segment, then response url.
        if not item.get("ref"):
            ref = None
            if isinstance(ld_item, dict):
                ref = ld_item.get("branchCode") or ld_item.get("@id") or ld_item.get("url")
            if not ref and item.get("website"):
                ref = item["website"]
            if not ref and response and response.url:
                ref = response.url

            if isinstance(ref, str):
                # normalize to last non-empty path segment
                parts = [p for p in ref.split("/") if p]
                if parts:
                    item["ref"] = parts[-1]
                else:
                    item["ref"] = ref
            else:
                item["ref"] = None

            # Fix opening hours: convert ISO datetimes to just HH:MM for each rule, and adjust closes by +12h if needed
            if isinstance(ld_item, dict) and "openingHoursSpecification" in ld_item:
                oh_spec = ld_item["openingHoursSpecification"]
                for rule in oh_spec:
                    for key in ("opens", "closes"):
                        val = rule.get(key)
                        if isinstance(val, str) and "T" in val:
                            # Extract just HH:MM from e.g. 2025-12-22T11:00:00.000Z
                            try:
                                rule[key] = val.split("T")[1][:5]
                            except Exception:
                                pass

                # Adjust closes by +12h if closes <= opens (i.e., closes in AM, but should be PM)
                def add_12h_if_needed(opens, closes):
                    try:
                        o_h, o_m = map(int, opens.split(":"))
                        c_h, c_m = map(int, closes.split(":"))
                        # If closes hour is less than or equal to opens, assume PM close (add 12h)
                        if c_h <= o_h:
                            c_h = (c_h + 12) % 24
                        return f"{c_h:02d}:{c_m:02d}"
                    except Exception:
                        return closes

                from locations.hours import OpeningHours

                item["opening_hours"] = OpeningHours()
                for rule in oh_spec:
                    day = rule.get("dayOfWeek")
                    opens = rule.get("opens")
                    closes = rule.get("closes")
                    if not (day and opens and closes):
                        continue
                    closes_adj = add_12h_if_needed(opens, closes)
                    days = [day] if isinstance(day, str) else day
                    for d in days:
                        item["opening_hours"].add_range(d, opens, closes_adj, "%H:%M")
        yield item
