import json
from typing import Any

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Extras, apply_yes_no
from locations.linked_data_parser import LinkedDataParser
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
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
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    allowed_domains = ["nandosperiperi.com"]
    start_urls = ["https://www.nandosperiperi.com/all-locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Try to find JSON-LD ItemList(s) on the page and extract location entries.
        scripts = response.xpath("//script[@type='application/ld+json']/text()").getall()
        for script in scripts:
            try:
                data = json.loads(script)
            except Exception:
                continue

            # normalize to list of objects
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                types = obj.get("@type")
                if not types:
                    continue
                if isinstance(types, list):
                    types_clean = [t.lower() for t in types]
                else:
                    types_clean = [str(types).lower()]

                if "itemlist" not in " ".join(types_clean):
                    continue

                # Found an ItemList — iterate its elements
                for element in obj.get("itemListElement", []) or []:
                    # element may be a ListItem wrapper
                    if isinstance(element, dict):
                        # Prefer embedded item data
                        if item_obj := element.get("item") or element.get("mainEntity"):
                            if isinstance(item_obj, dict):
                                # Parse linked data directly, passing spider time_format
                                item = LinkedDataParser.parse_ld(item_obj, time_format=self.time_format)
                                # Use post_process_item to keep consistency
                                yield from self.post_process_item(item, response, item_obj)
                                continue

                        # Otherwise, try to follow a URL
                        url = element.get("url") or element.get("@id")
                        if url:
                            yield response.follow(response.urljoin(url), callback=self.parse_sd)
                            continue

                    # Fallback: if element is a string URL
                    if isinstance(element, str) and element.startswith("http"):
                        yield response.follow(response.urljoin(element), callback=self.parse_sd)

        # Fall back to CrawlSpider behaviour (rules) if nothing yielded above
        return super().parse(response, **kwargs)

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
        item["website"] = response.url
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
        yield item
