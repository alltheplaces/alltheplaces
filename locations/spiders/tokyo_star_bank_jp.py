import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TokyoStarBankJPSpider(Spider):
    name = "tokyo_star_bank_jp"
    item_attributes = {
        "brand": "Tokyo Star Bank",
        "brand_wikidata": "Q7813998",
    }
    start_urls = ["https://www.tokyostarbank.co.jp/lounge_atm/"]

    # Pages in the lounge_atm directory that are not physical branch locations
    SKIP_SLUGS = {
        "consultation_limited",
        "orangeport",
        "integration",
    }

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for href in response.css("a[href]::attr(href)").getall():
            m = re.match(r"^/lounge_atm/([a-z_]+)\.html$", href)
            if m and m.group(1) not in self.SKIP_SLUGS:
                yield response.follow(href, callback=self.parse_branch)

    def parse_branch(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page uses Shift-JIS but Scrapy decodes it automatically via the charset meta tag
        table = response.css("table.table__matrix")
        if not table:
            return

        # Build a dict from the table: th text -> td text/html
        rows = {}
        for tr in table.css("tbody tr"):
            th = tr.css("th::text").get("").strip()
            # Collect text including <br> newlines
            td_parts = []
            for node in tr.css("td *::text, td::text"):
                td_parts.append(node.get().strip())
            rows[th] = " ".join(p for p in td_parts if p)

        # Store number is the stable unique ID
        ref = rows.get("店番", "").strip()
        if not ref:
            return

        # Japanese address (住所): strip postal code prefix
        addr_raw = rows.get("住所", "")
        addr_full = re.sub(r"〒\d{3}-\d{4}\s*", "", addr_raw).strip()
        if not addr_full:
            return  # No physical address — skip (e.g. internet-only branches)

        branch_name = response.css("h1.heading1__title::text").get("").strip()

        # Phone: first tel: link href
        phone_raw = response.css('a[href^="tel:"]::attr(href)').get("")
        phone = phone_raw.replace("tel:", "").strip() if phone_raw else None

        item = Feature()
        item["ref"] = ref
        item["branch"] = branch_name
        item["addr_full"] = addr_full
        item["country"] = "JP"
        item["phone"] = phone
        item["website"] = response.url

        # Opening hours: parse the 営業時間：窓口 (counter/teller hours) row
        oh_key = next((k for k in rows if k.startswith("営業時間：窓口")), None)
        if oh_key:
            item["opening_hours"] = self._parse_opening_hours(response, oh_key)

        apply_category(Categories.BANK, item)

        yield item

    def _parse_opening_hours(self, response: Response, row_key: str) -> OpeningHours:
        oh = OpeningHours()

        # Find the <tr> whose <th> text starts with the given key
        for tr in response.css("table.table__matrix tbody tr"):
            th = tr.css("th::text").get("").strip()
            if not th.startswith(row_key):
                continue

            # Extract the <li> text items from the hours list
            items = [li.css("::text").getall() for li in tr.css("ul.unorder-list li")]
            for parts in items:
                line = "".join(parts).strip()
                # Line looks like: "平日　9:00～15:00" or "土曜　休業" etc.
                # Normalise fullwidth tilde and spaces
                line = line.replace("〜", "-").replace("〜", "-").replace("～", "-")
                line = re.sub(r"\s+", " ", line)

                # Split on first space to get day and time
                parts2 = line.split(" ", 1)
                if len(parts2) != 2:
                    continue
                day_ja, time_part = parts2[0].strip(), parts2[1].strip()

                if "休業" in time_part or "休み" in time_part:
                    continue  # closed — skip (OpeningHours omits closed days)

                # Map Japanese day names to OSM weekday abbreviations
                day_map = {
                    "平日": "Mo-Fr",
                    "土曜": "Sa",
                    "日曜": "Su",
                    "祝日": "PH",
                }
                osm_day = day_map.get(day_ja)
                if not osm_day:
                    continue

                # time_part looks like "9:00-15:00"
                time_match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", time_part)
                if not time_match:
                    continue

                open_time, close_time = time_match.group(1), time_match.group(2)
                # Pad to HH:MM
                open_time = open_time.zfill(5)
                close_time = close_time.zfill(5)

                oh.add_ranges_from_string(f"{osm_day} {open_time}-{close_time}")
            break

        return oh
