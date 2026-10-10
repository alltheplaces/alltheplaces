import base64
import json
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PttTRSpider(Spider):
    name = "ptt_tr"
    item_attributes = {"operator": "PTT", "operator_wikidata": "Q3079259"}
    allowed_domains = ["enyakinptt.ptt.gov.tr"]
    API = "https://enyakinptt.ptt.gov.tr/api/"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(f"{self.API}il", callback=self.parse_provinces)

    @staticmethod
    def decode(response: Response) -> Any:
        # The "nearest PTT" finder returns Base64-encoded JSON.
        return json.loads(base64.b64decode(response.body))

    def parse_provinces(self, response: Response, **kwargs: Any) -> Any:
        for province in self.decode(response):
            # ilceID=0 and mahKoyID=0 return every workplace in the province.
            yield FormRequest(
                f"{self.API}Isyerleri",
                formdata={"ilID": str(province["Kod"]), "ilceID": "0", "mahKoyID": "0"},
                callback=self.parse,
                cb_kwargs={"province": province["Ad"]},
            )

    def parse(self, response: Response, province: str) -> Any:
        for office in self.decode(response):
            item = Feature()
            item["ref"] = str(office["Sira"])
            item["lat"], item["lon"] = office["Lat"], office["Lon"]
            item["addr_full"] = office["Adres"]
            item["state"] = province
            item["phone"] = office["Telefon"]
            name = re.sub(r"\s+", " ", office["Ad"]).strip()
            if office["Cins"] == "ACENTELİK":
                # PTT agencies are run by third parties (municipalities, businesses, village heads).
                item["name"] = f"PTT {name}"
                item["extras"]["post_office"] = "post_partner"
                apply_category(Categories.GENERIC_POI, item)
            elif re.search(r"DAĞITIM|İŞLEME|AKTARMA", name):
                # Delivery, sorting and transfer centres ("POSTA DAĞITIM MÜDÜRLÜĞÜ" etc.)
                item["branch"] = name
                apply_category(Categories.POST_DEPOT, item)
            else:
                # "MERKEZ" (main offices) and "ŞUBE" (branches).
                item["branch"] = name
                apply_category(Categories.POST_OFFICE, item)
            item["opening_hours"] = self.parse_hours(office)
            yield item

    @staticmethod
    def parse_hours(office: dict) -> OpeningHours:
        # e.g. "08:30-12:30/13:30-17:00", "08:30-17:00/-" or "KAPALI" (closed)
        oh = OpeningHours()
        for days, text in (
            (DAYS[:5], office.get("HaftaIci")),
            (["Sa"], office.get("Cumartesi")),
            (["Su"], office.get("Pazar")),
        ):
            ranges = []
            found = re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", text or "")
            for start, end in sorted((s.zfill(5), e.zfill(5)) for s, e in found):
                if start >= end:
                    continue  # placeholders such as "00:00-00:00" or "08:30-08:30"
                if ranges and start <= ranges[-1][1]:
                    ranges[-1][1] = max(ranges[-1][1], end)  # overlapping or touching ranges
                else:
                    ranges.append([start, end])
            for start, end in ranges:
                for day in days:
                    oh.add_range(day, start, end)
        return oh
