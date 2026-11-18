import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_DE, DELIMITERS_DE, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "Liechtensteinische Post", "operator_wikidata": "Q1840786"}


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
        # The page has no ids: type plus rounded position.
        item["ref"] = f"{kind.lower()}-{float(lat):.5f},{float(lon):.5f}"
        return item

    @staticmethod
    def parse_collection_times(text: str) -> str:
        # "Mo-Fr: 16:00  Sa: 08:00", "Sa: keine Leerung", "Sa: 07.30"
        out = []
        for start, end, time in re.findall(r"\b([A-Za-z]{2})(?:\s*-\s*([A-Za-z]{2}))?\s*:\s*(\d{1,2}[:.]\d{2})", text):
            start, end = DAYS_DE.get(start.title()), DAYS_DE.get((end or start).title())
            if start and end:
                days = f"{start}-{end}" if start != end else start
                out.append(f"{days} {time.replace('.', ':').zfill(5)}")
        return "; ".join(out)

    @staticmethod
    def parse_hours(rows) -> OpeningHours:
        # Rows are "<p>Mo-Fr:</p> <p>07:45-12:00</p>"; a row with no day continues the previous one.
        text = " ".join(" ".join(row.css("::text").getall()) for row in rows)
        oh = OpeningHours()
        if "24 Stunden" in text:
            oh.add_days_range(DAYS, "00:00", "24:00")
        else:
            oh.add_ranges_from_string(text, days=DAYS_DE, delimiters=DELIMITERS_DE)
        return oh
