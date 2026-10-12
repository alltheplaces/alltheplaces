import re
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The finder has no office-type field, so offices that are not public counters are recognised by their names:
# administrative offices ("VP BĐH", "Văn phòng"), mail processing and transport centres ("KT", "Khai thác", "KTVC"),
# delivery-only offices ("BCP", "Tổ Bưu tá"), large-customer units ("KHL"), the government mail network ("Hệ 1"),
# public-administration service desks ("HCC", "Hành chính công"), newspaper distribution ("PHBC"), parcel hubs, and
# anything marked as suspended ("tạm dừng").
NOT_PUBLIC = re.compile(
    r"^vp|văn phòng|^kt\d?\b|khai thác|ktvc|^bcp\b|bưu tá|^phát tại|\bkhl\b|^hệ 1|\bhcc\b|hành chính công|^phbc|\bhub\b"
    r"|tạm dừng|tạm ngừng|tạm ngưng|ngừng hoạt động|đóng cửa|giải thể"
)
PARTNER = re.compile(r"^đl\b|^đlbđ\b|đại lý")  # "Đại lý (Bưu điện)": postal agencies run by third parties
POST_BOX = re.compile(r"^thùng thư|^hòm thư")  # public letter boxes listed alongside the offices


class VietnamPostVNSpider(Spider):
    name = "vietnam_post_vn"
    item_attributes = {"operator": "Vietnam Post", "operator_wikidata": "Q112150791"}
    allowed_domains = ["vietnampost.vn"]
    # The "Tìm Bưu Cục" finder on vietnampost.vn searches a province plus one commune/ward ("districts" returns the
    # post-2025 communes); a search without a commune adds the few offices that are not linked to one.
    api = "https://vietnampost.vn/vnpost/"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(f"{self.api}address/provinces", callback=self.parse_provinces)

    def search_url(self, path: str, province_id: str, commune_id: str = "") -> str:
        query = {"district_id": commune_id, "province_id": province_id, "district_code": "", "province_code": ""}
        return f"{self.api}{path}?{urlencode(query)}"

    def parse_provinces(self, response: Response) -> Any:
        # A search without a commune ignores the province and returns the same offices that are not linked to
        # any commune (about 20, all over the country), so it is made once and the province is not set.
        yield JsonRequest(
            self.search_url("post-office", response.json()[0]["ProvinceId"]),
            callback=self.parse_offices,
            cb_kwargs={"state": None},
        )
        for province in response.json():
            province_id = province["ProvinceId"]
            state = re.sub(r"^(TP\.|Tỉnh)\s*", "", province["ProvinceFullName"]).strip()
            yield JsonRequest(
                self.search_url("address/districts", province_id),
                callback=self.parse_communes,
                cb_kwargs={"province_id": province_id, "state": state},
            )

    def parse_communes(self, response: Response, province_id: str, state: str) -> Any:
        for commune in response.json():
            yield JsonRequest(
                self.search_url("post-office", province_id, commune["CommuneID"]),
                callback=self.parse_offices,
                cb_kwargs={"state": state},
            )

    def parse_offices(self, response: Response, state: str | None) -> Any:
        for office in response.json():
            name = re.sub(r"\s+", " ", office.get("PostOfficeName") or "").strip()
            lower = name.lower()
            if NOT_PUBLIC.search(lower):
                continue

            item = Feature()
            item["ref"] = str(office["PostOfficeId"] or office["PostCode"])  # a few offices have no PostOfficeId
            lat, lon = office.get("lat"), office.get("lng")
            if lat and lon and abs(float(lat)) > 90:  # the finder's own map swaps these back too
                lat, lon = lon, lat
            item["lat"], item["lon"] = lat, lon
            item["street_address"] = re.sub(r"\s+", " ", office.get("DetailsAddress") or "").strip(" ,")
            item["state"] = state

            if POST_BOX.search(lower):
                apply_category(Categories.POST_BOX, item)
                yield item
                continue

            item["postcode"] = office.get("PostCode")
            item["phone"] = self.clean_phone(office.get("TelexNo"))
            if PARTNER.search(lower):
                item["name"] = name
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                item["branch"] = name
                apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def clean_phone(phone: str | None) -> str | None:
        # Numbers are mostly stored without the trunk prefix, e.g. "2439271693" for 024 3927 1693. Pre-2018 numbers
        # (short local numbers, 11-digit "01x" mobiles) no longer work and are dropped.
        digits = re.sub(r"\D", "", phone or "")
        if len(digits) in (9, 10) and not digits.startswith("0"):
            digits = f"0{digits}"
        return digits if len(digits) == 10 else None
