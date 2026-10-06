import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "Liechtensteinische Post", "operator_wikidata": "Q1840786"}
DAYS_LI = {"mo": "Mo", "di": "Tu", "mi": "We", "do": "Th", "fr": "Fr", "sa": "Sa", "so": "Su"}


def parse_days(text: str) -> list[str]:
    # "Mo-Fr", "Sa", "Mo-So"
    names = [DAYS_LI[d.lower()] for d in re.findall(r"\b(Mo|Di|Mi|Do|Fr|Sa|So)\b", text, re.I)]
    if len(names) == 2 and "-" in text:
        return DAYS[DAYS.index(names[0]) : DAYS.index(names[1]) + 1]
    return names


class LiechtensteinischePostLiSpider(Spider):
    name = "liechtensteinische_post_li"
    allowed_domains = ["post.li"]
    # One WordPress page with every location as a map marker (data-cats, data-lat, data-lng).
    start_urls = ["https://post.li/standorte/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for marker in response.css("div.marker[data-lat]"):
            cats = marker.attrib.get("data-cats", "").split()
            lat, lon = marker.attrib["data-lat"], marker.attrib["data-lng"]
            label = (marker.css("[data-permalink]::attr(data-permalink)").get() or "").strip()
            if "Postfiliale" in cats or "Postpartner" in cats:
                item = self.base_item(lat, lon, cats[0])
                item["opening_hours"] = self.parse_hours(marker.css("div.offe div.days__open__wrapper"))
                if "Postfiliale" in cats:
                    item.update(OPERATOR)
                    item["branch"] = label.removeprefix("Postfiliale").strip() or None
                    apply_category(Categories.POST_OFFICE, item)
                else:
                    # Post counters run by local shops.
                    item["name"] = label or None
                    item["extras"]["post_office"] = "post_partner"
                    item["extras"]["post_office:brand"] = OPERATOR["operator"]
                    item["extras"]["post_office:brand:wikidata"] = OPERATOR["operator_wikidata"]
                    apply_category(Categories.GENERIC_POI, item)
                yield item
            if "Briefeinwurf" in cats:
                item = self.base_item(lat, lon, "Briefeinwurf")
                item.update(OPERATOR)
                if label:
                    item["extras"]["description"] = label.removeprefix("Briefeinwurf").strip()
                text = " ".join(marker.css("div.letzte div.days__open__wrapper ::text").getall())
                if collection_times := self.parse_collection_times(text):
                    item["extras"]["collection_times"] = collection_times
                apply_category(Categories.POST_BOX, item)
                yield item
            # Not emitted: parcel lockers ("Paketautomat") and business customer counters
            # ("Geschäftskundenschalter").

    @staticmethod
    def base_item(lat: str, lon: str, kind: str) -> Feature:
        item = Feature()
        item["lat"], item["lon"] = lat, lon
        item["country"] = "LI"
        # The page has no ids: type plus rounded position.
        item["ref"] = f"{kind.lower()}-{float(lat):.5f},{float(lon):.5f}"
        return item

    @staticmethod
    def parse_collection_times(text: str) -> str:
        # "Mo-Fr: 16:00  Sa: 08:00", "Sa: keine Leerung", "Sa: 07.30"
        out = []
        for days, time in re.findall(r"([A-Za-z]{2}(?:\s*-\s*[A-Za-z]{2})?)\s*:\s*(\d{1,2}[:.]\d{2})", text):
            if day_list := parse_days(days):
                days = f"{day_list[0]}-{day_list[-1]}" if len(day_list) > 1 else day_list[0]
                out.append(f"{days} {time.replace('.', ':').zfill(5)}")
        return "; ".join(out)

    @staticmethod
    def parse_hours(rows) -> OpeningHours:
        # Each row is "<p>Mo-Fr:</p> <p>07:45-12:00</p>"; a row with no day continues the previous one.
        oh = OpeningHours()
        days: list[str] = []
        for row in rows:
            text = " ".join(row.css("::text").getall())
            if "24 Stunden" in text:
                oh.add_days_range(DAYS, "00:00", "24:00")
                continue
            days = parse_days(text.split(":")[0]) or days
            for start, end in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", text):
                oh.add_days_range(days, start, end)
        return oh
