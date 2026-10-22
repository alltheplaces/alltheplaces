import json
import re
from html import unescape
from itertools import groupby
from typing import Any

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_3_LETTERS, DAYS_EN, OpeningHours, day_range
from locations.items import Feature


def days_of(text: str) -> list[str]:
    # "Mon - Fri", "Monday - Sunday", "Sat", "Sunday"
    names = [DAYS_EN[d.title()] for d in re.findall(rf"\b({'|'.join(DAYS_3_LETTERS)})[a-z]*", text, re.I)]
    if len(names) >= 2 and "-" in text:
        return day_range(names[0], names[1])
    return names


class IomPostIMSpider(Spider):
    name = "iom_post_im"
    item_attributes = {"operator": "Isle of Man Post Office", "operator_wikidata": "Q3432267"}
    allowed_domains = ["www.iompost.com"]
    # The services finder embeds every post box as a JS array (markerNodes); post offices are a
    # separate layer (service 23) loaded by getServiceNodes.php.
    start_urls = ["https://www.iompost.com/tools-forms/post-office-services-finder/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        nodes = re.search(r"var\s+markerNodes\s*=\s*\[(.*?)\];", response.text, re.DOTALL).group(1)
        for node in re.findall(r"\{(.*?)\}", nodes, re.DOTALL):
            fields = dict(re.findall(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'", node))
            name = unescape(fields.get("name", "")).strip()
            if not name or "parcel box" in name.lower():
                continue
            item = self.base_item(name, fields.get("lat"), fields.get("lng"))
            item["extras"]["description"] = name.title() if name.isupper() else name
            if collection_times := self.parse_collection_times(unescape(fields.get("collection", ""))):
                item["extras"]["collection_times"] = collection_times
            apply_category(Categories.POST_BOX, item)
            yield item
        yield FormRequest(
            "https://www.iompost.com/assets/ajax/getServiceNodes.php",
            formdata={"service": "23"},
            callback=self.parse_offices,
        )

    def parse_offices(self, response: Response) -> Any:
        for office in json.loads(response.text):
            name = unescape(office["name"]).strip()
            item = self.base_item(name, office["lat"], office["lng"])
            item["branch"] = re.sub(r"\s*Post Office$", "", name)
            text = re.sub(r"<br\s*/?>", "\n", unescape(office.get("collection") or ""))
            text = re.sub(r"<[^>]+>", "", text)
            # "09.00 - 12.30 & 13.30 - 17.30" -> "09:00 - 12:30, 13:30 - 17:30"
            hours = re.sub(r"(\d)\.(\d{2})", r"\1:\2", text)
            hours = re.sub(r"(\d)\s*&\s*(\d)", r"\1, \2", hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)
            if m := re.search(r"(IM\d{1,2}\s*\d[A-Z]{2})", text):
                item["postcode"] = m.group(1)
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def base_item(name: str, lat: str, lon: str) -> Feature:
        item = Feature()
        item["lat"], item["lon"] = str(lat).strip(" ,"), str(lon).strip(" ,")
        # No ids in the source: name plus rounded position.
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        item["ref"] = f"{slug}-{float(item['lat']):.4f},{float(item['lon']):.4f}"
        return item

    @staticmethod
    def parse_collection_times(text: str) -> str:
        times = {}
        for line in re.split(r"<br\s*/?>|\n", text):
            for t in re.findall(r"\d{1,2}:\d{2}", line):
                for day in days_of(line):
                    times.setdefault(day, set()).add(t.zfill(5))
        by_day = {day: ",".join(sorted(v)) for day, v in times.items()}
        out = []
        for time, days in groupby(DAYS, key=by_day.get):
            if time:
                days = list(days)
                out.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(out)
