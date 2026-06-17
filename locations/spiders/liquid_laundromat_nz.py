import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class LiquidLaundromatNZSpider(Spider):
    name = "liquid_laundromat_nz"
    item_attributes = {"brand": "Liquid Laundromat", "brand_wikidata": "Q131362924"}
    start_urls = ["https://liquidlaundromats.com/nz/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css(".location-item"):
            item = Feature()
            item["lat"] = location.attrib.get("data-lat")
            item["lon"] = location.attrib.get("data-lng")

            raw_name = location.css("h5::text").get("").strip()
            item["branch"] = raw_name.removeprefix("Liquid Laundromat").lstrip(" -").strip()

            address_text = location.css("address::text").get("").strip()
            self._parse_address(item, address_text)

            detail_link = location.css("a.button[href*='/locations/']::attr(href)").getall()
            detail_link = [h for h in detail_link if "maps.google" not in h]
            if detail_link:
                item["ref"] = detail_link[0].rstrip("/").split("/")[-1]
                item["website"] = detail_link[0]
            else:
                item["ref"] = raw_name

            hours_rows = location.css(".hours li")
            if hours_rows:
                item["opening_hours"] = self._parse_hours(hours_rows)

            apply_category(Categories.SHOP_LAUNDRY, item)
            yield item

    def _parse_address(self, item: Feature, address: str) -> None:
        address = re.sub(r",?\s*New Zealand\s*$", "", address.strip())
        parts = [p.strip() for p in address.split(",") if p.strip()]
        if not parts:
            return
        item["street_address"] = parts[0]
        item["country"] = "NZ"
        if len(parts) >= 2:
            last = parts[-1]
            pc_match = re.search(r"\b(\d{4})\b", last)
            if pc_match:
                item["postcode"] = pc_match.group(1)
                item["city"] = re.sub(r"\s*\d{4}\s*$", "", last).strip()
            elif len(parts) >= 3:
                penult = parts[-2]
                pc2 = re.search(r"\b(\d{4})\b", penult)
                if pc2:
                    item["postcode"] = pc2.group(1)
                    item["city"] = re.sub(r"\s*\d{4}\s*$", "", penult).strip()
                else:
                    item["city"] = penult
            else:
                item["city"] = last

    def _parse_hours(self, hours_rows: Any) -> OpeningHours:
        oh = OpeningHours()
        for row in hours_rows:
            day = row.css("strong::text").get("").strip()
            time_str = row.css("span::text").get("").strip()
            if not day or not time_str:
                continue
            combined = f"{day} {time_str}".strip()
            combined = re.sub(r"\b7\s+days?\b", "Mo-Su", combined, flags=re.IGNORECASE)
            combined = re.sub(r"\bOpen\s+7\s+days?\b", "Mo-Su", combined, flags=re.IGNORECASE)
            combined = combined.replace("Mon-Sun", "Mo-Su").replace("Mon-Sat", "Mo-Sa")
            combined = re.sub(r"\b24/7\b", "00:00-24:00", combined)
            combined = re.sub(r"\bOpen\s+24\s+hours?\b", "00:00-24:00", combined, flags=re.IGNORECASE)
            combined = re.sub(r"\b24\s+hours?\b", "00:00-24:00", combined, flags=re.IGNORECASE)
            combined = re.sub(r"\bOpen\s+(\d)", r"\1", combined)
            oh.add_ranges_from_string(combined.strip())
        return oh
