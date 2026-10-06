import json
import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


class PosteSrpskeBaSpider(Spider):
    name = "poste_srpske_ba"
    item_attributes = {"operator": "Pošte Srpske", "operator_wikidata": "Q5245881"}
    allowed_domains = ["www.postesrpske.com"]
    start_urls = ["https://www.postesrpske.com/pronadji-poste/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The page embeds two "Ultimate Maps by Supsystic" maps with the same offices: one in Cyrillic
        # (Serbian labels) and one in Latin script (English labels), each with its own marker ids.
        # Only the Latin copy is used.
        decoder = json.JSONDecoder()
        seen = set()
        for match in re.finditer(r'"markers":\[', response.text):
            markers, _ = decoder.raw_decode(response.text, match.end() - 1)
            for marker in markers:
                if CYRILLIC_RE.search(marker["title"]) or marker["id"] in seen:
                    continue
                seen.add(marker["id"])
                if item := self.parse_marker(marker):
                    yield item

    def parse_marker(self, marker: dict) -> Feature | None:
        title = re.sub(r"\s+", " ", marker["title"]).strip()  # "74270 Teslić (Izdvojeni šalter - Đulić)"
        if "Brza pošta" in title:
            return None  # express/courier unit, not a post office counter
        # Description: "Address: ...<br/>Phone: 1371<br/>Working hours (mon-fri): 07:00 - 15:00<br/>Working hours (sat): <br/>"
        fields = {}
        for line in Selector(text=marker["description"] or "").xpath("//body//text()").getall():
            label, _, value = line.partition(":")
            fields[label.strip().lower()] = value.strip()

        item = Feature()
        item["ref"] = marker["id"]
        item["lat"], item["lon"] = marker["coord_x"], marker["coord_y"]  # coord_x is the latitude
        if m := re.match(r"(\d{5})\s*(.*)", title):
            item["postcode"], item["branch"] = m.group(1), m.group(2)
        else:
            item["branch"] = title
        item["street_address"] = fields.get("address") or None
        # "Phone" is always the 1371 call centre short number (or empty), so it is not kept.
        oh = OpeningHours()
        for key, days in (("working hours (mon-fri)", DAYS[:5]), ("working hours (sat)", ["Sa"])):
            times = re.findall(r"(\d{1,2}[:.]\d{2})\s*-\s*(\d{1,2}[:.]\d{2})", fields.get(key, ""))
            for start, end in times:
                oh.add_days_range(days, start.replace(".", ":"), end.replace(".", ":"))
        item["opening_hours"] = oh
        # Detached counters ("Izdvojeni šalter") are staffed by Pošte Srpske as well.
        apply_category(Categories.POST_OFFICE, item)
        return item
