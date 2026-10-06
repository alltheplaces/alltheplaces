import re
from html import unescape
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

DAYS_HR = {"Pon": "Mo", "Uto": "Tu", "Sri": "We", "Čet": "Th", "Pet": "Fr", "Sub": "Sa", "Ned": "Su"}


class HrvatskaPostaHRSpider(Spider):
    name = "hrvatska_posta_hr"
    item_attributes = {"operator": "Hrvatska pošta", "operator_wikidata": "Q507289"}
    allowed_domains = ["www.posta.hr"]
    # The network map embeds every post office ("pu"), letter box ("kov") and parcel locker ("pak") as
    # three parallel arrays: vrsta[i] (type), content[i] (info window HTML) and neighborhoods[i] (position).
    start_urls = ["https://www.posta.hr/hp-mreza-postanskih-ureda-kovcezica-i-paketomata"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        html = response.text
        kinds = {int(i): k for i, k in re.findall(r"vrsta\[(\d+)\]\s*=\s*'([a-z]+)'", html)}
        contents = {int(i): c for i, _, c in re.findall(r"content\[(\d+)\]\s*=\s*(['\"])(.*?)\2\s*;", html, re.DOTALL)}
        positions = re.search(r"var\s+neighborhoods\s*=\s*\[(.*?)\];", html, re.DOTALL).group(1)
        coords = re.findall(r"LatLng\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", positions)
        for i, (lat, lon) in enumerate(coords):
            kind = kinds.get(i)
            if kind not in ("pu", "kov"):
                continue
            lines = [unescape(t).strip() for t in re.split(r"<[^>]+>", contents.get(i, ""))]
            lines = [t for t in lines if t]
            if len(lines) < 3:
                continue
            item = Feature()
            item["lat"], item["lon"] = lat, lon
            # lines: [kind label, "<office postcode>[-<box no>] <PLACE>", "<street>", ...]
            code, _, place = lines[1].partition(" ")
            item["ref"] = code
            item["city"] = place.title()
            item["street_address"] = lines[2]
            if kind == "kov":
                item["postcode"] = code.split("-")[0]
                apply_category(Categories.POST_BOX, item)
            else:
                item["postcode"] = code
                item["branch"] = place.title()
                item["opening_hours"] = self.parse_hours(lines)
                apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours:
        # "... Pon:", "7:00-24:00", "Uto:", "7:00-24:00", ... (a missing range means closed)
        oh = OpeningHours()
        for label, value in zip(lines, lines[1:]):
            day = DAYS_HR.get(label.rstrip(":"))
            if not day:
                continue
            for start, end in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", value):
                oh.add_range(day, start, end)
        return oh
