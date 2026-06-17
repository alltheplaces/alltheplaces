import html
import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class RapidCoutureFRSpider(scrapy.Spider):
    name = "rapid_couture_fr"
    item_attributes = {"brand": "Rapid' Couture", "brand_wikidata": "Q120664654", "country": "FR"}
    start_urls = ["https://www.rapid-couture.com/les-ateliers/"]

    def parse(self, response: Response, **kwargs: Any):
        # Location list is embedded as JavaScript array `var ateliers = [...]` in the page
        m = re.search(r"var ateliers\s*=\s*(\[.*?\]);", response.text, re.DOTALL)
        if not m:
            self.logger.error("Could not find 'var ateliers' data on %s", response.url)
            return

        ateliers = json.loads(m.group(1))
        for atelier in ateliers:
            # Skip if no coordinates
            lat = atelier.get("latitude")
            lon = atelier.get("longitute")  # typo in source
            if not lat or not lon:
                continue

            item = Feature()
            item["ref"] = str(atelier.get("id"))
            # Location names are "Rapid couture – CITY" variants; put the city part in branch
            raw_name = html.unescape(atelier.get("nom", ""))
            item["branch"] = re.sub(
                r"^Rapid[\s'\u2019]couture\s*[\u2013-]\s*", "", raw_name, flags=re.IGNORECASE
            ).strip()
            if not item["branch"]:
                item["branch"] = raw_name
            item["street_address"] = atelier.get("add1", "").strip()
            # add2 is generally empty but append if present
            add2 = atelier.get("add2", "").strip()
            if add2:
                item["street_address"] = f"{item['street_address']}, {add2}"
            item["postcode"] = atelier.get("code", "").strip()
            item["city"] = atelier.get("ville", "").strip()
            item["lat"] = float(lat)
            item["lon"] = float(lon)
            item["website"] = atelier.get("link", "")

            apply_category(Categories.SHOP_TAILOR, item)

            # Fetch the individual atelier page for phone and opening hours
            if item["website"]:
                yield scrapy.Request(
                    url=item["website"],
                    callback=self.parse_atelier,
                    cb_kwargs={"item": item},
                )
            else:
                yield item

    def parse_atelier(self, response: Response, item: Feature, **kwargs: Any):
        # Extract phone number
        phone_span = response.xpath('//span[contains(@class,"tel_fra")]/following-sibling::text()').get("")
        if not phone_span:
            phone_text = response.xpath('//p[span[contains(@class,"tel_fra")]]/text()').get("")
            if phone_text:
                phone_span = phone_text.strip()
        if phone_span:
            phone = re.sub(r"\s+", " ", phone_span.strip())
            if re.search(r"\d{2}", phone):
                item["phone"] = phone

        # Extract opening hours from the <div class="horaires"> section
        hours_div = response.xpath('//div[contains(@class,"horaires")]')
        if hours_div:
            oh = self.parse_hours(hours_div.xpath("string()").get(""))
            if oh:
                item["opening_hours"] = oh

        yield item

    def parse_hours(self, text: str) -> str | None:
        oh = OpeningHours()
        found = False
        for line in text.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            # Format: "Lundi : 09h30-13h00 & 14h00-18h00" or "Lundi : Fermé"
            # (some entries omit the space before the colon: "Lundi: ...")
            parts = re.split(r"\s*:\s*", line, 1)
            if len(parts) != 2:
                continue
            day_str = parts[0].strip()
            times_str = parts[1].strip().replace("&#038;", "&")
            day = DAYS_FR.get(day_str)
            if not day:
                continue
            if "fermé" in times_str.lower():
                oh.set_closed(day)
                found = True
                continue
            # Can have multiple ranges separated by & or " & "
            for time_range in re.split(r"\s*&\s*", times_str):
                time_range = time_range.strip()
                m = re.match(r"(\d{1,2})h(\d{2})-(\d{1,2})h(\d{2})", time_range)
                if m:
                    open_h, open_m, close_h, close_m = m.groups()
                    oh.add_range(
                        day,
                        f"{int(open_h):02d}:{open_m}",
                        f"{int(close_h):02d}:{close_m}",
                    )
                    found = True
        return oh if found else None
