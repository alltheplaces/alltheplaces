import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAYS_IT_ORDER = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"]

# Italian address format: "Street Number, POSTCODE City PROV"
ADDRESS_RE = re.compile(r"^(.*),\s*(\d{5})\s+(.*)\s+[A-Z]{2}$")


class PiumeITSpider(CSVFeedSpider):
    name = "piume_it"
    item_attributes = {
        "brand": "Piùme",
        "brand_wikidata": "Q113579745",
        "country": "IT",
    }
    start_urls = ["https://connettore.piume.it/storelocator/stores.csv"]

    def parse_row(self, response: Response, row: dict[str, str]) -> Any:
        if row.get("TYPE") != "STORE":
            return

        item = Feature()
        item["ref"] = row["uuid"]
        item["lat"] = row["Ycoord"] or None
        item["lon"] = row["Xcoord"] or None

        # Parse Italian address: "Street, POSTCODE City PROV"
        addr = row["indirizzo"].strip()
        m = ADDRESS_RE.match(addr)
        if m:
            item["street_address"] = m.group(1).strip()
            item["postcode"] = m.group(2)
            item["city"] = m.group(3).strip()
        else:
            item["street_address"] = addr

        item["state"] = row.get("regione", "").strip() or None

        phone = row.get("telefono_negozio", "").strip()
        if phone and phone != "0584 753333":  # shared corporate number
            item["phone"] = phone

        item["opening_hours"] = self._parse_hours(row)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item

    def _parse_hours(self, row: dict[str, str]) -> OpeningHours | None:
        oh = OpeningHours()
        has_hours = False
        for csv_day, osm_day in zip(DAYS_IT_ORDER, DAYS):
            raw = row.get(csv_day, "").strip().lower()
            if not raw or raw == "chiuso":
                continue
            parts = [t.strip() for t in raw.split(",")]
            # Expect pairs of times: open1, close1[, open2, close2]
            if len(parts) == 2:
                oh.add_range(osm_day, self._norm(parts[0]), self._norm(parts[1]))
                has_hours = True
            elif len(parts) == 4:
                oh.add_range(osm_day, self._norm(parts[0]), self._norm(parts[1]))
                oh.add_range(osm_day, self._norm(parts[2]), self._norm(parts[3]))
                has_hours = True
        return oh if has_hours else None

    @staticmethod
    def _norm(t: str) -> str:
        """Convert '08.30' or '8.30' to '08:30'."""
        return t.replace(".", ":").zfill(5)
