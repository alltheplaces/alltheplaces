import io
import re
from itertools import groupby
from typing import Any

import openpyxl
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_SK, day_range
from locations.items import Feature


class SlovenskaPostaPostboxesSKSpider(Spider):
    name = "slovenska_posta_postboxes_sk"
    item_attributes = {"operator": "Slovenská pošta", "operator_wikidata": "Q1191849"}
    allowed_domains = ["www.posta.sk"]
    # Linked from the branch finder's downloads (https://www.posta.sk/pobocky-a-balikoboxy).
    start_urls = ["https://www.posta.sk/files/6811e10225b182cd7cd9e3b9/zoznam-postovych-schranok.xlsx"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        sheet = openpyxl.load_workbook(io.BytesIO(response.body), read_only=True).active
        seen = {}
        for row in list(sheet.iter_rows(values_only=True))[1:]:
            number, office, placement, address, lat, lon, times = row[:7]
            if lat is None or lon is None:
                continue
            # A box number is unique only within its office, and a few repeat even there.
            ref = f"{office} {number}"
            seen[ref] = seen.get(ref, 0) + 1
            item = Feature()
            item["ref"] = ref if seen[ref] == 1 else f"{ref}-{seen[ref]}"
            item["lat"], item["lon"] = lat, lon
            item["addr_full"] = re.sub(r"\s+", " ", str(address or "")).strip(" ,")
            if m := re.search(r"\b(\d{3}) ?(\d{2})\s+(.+)$", item["addr_full"]):
                item["postcode"], item["city"] = m.group(1) + m.group(2), m.group(3).strip()
            item["extras"]["description"] = placement
            if collection_times := self.parse_collection_times(str(times or "")):
                item["extras"]["collection_times"] = collection_times
            apply_category(Categories.POST_BOX, item)
            yield item

    @staticmethod
    def parse_collection_times(text: str) -> str:
        # "po-pi:13:30/dnes" or "po:13:30/dnes ut:13:30/zmeškané …" (the suffix says whether the
        # post leaves the same day).
        times = {}
        for days, time in re.findall(r"([a-zš]{2}(?:-[a-zš]{2})?):(\d{1,2}:\d{2})", text):
            first, _, last = days.partition("-")
            first, last = DAYS_SK.get(first.title()), DAYS_SK.get((last or first).title())
            if not first or not last:
                continue
            for day in day_range(first, last):
                times[day] = time.zfill(5)
        collection_times = []
        for time, days in groupby(DAYS, key=times.get):
            if time:
                days = list(days)
                collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(collection_times)
