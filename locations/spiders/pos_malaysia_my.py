import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_EN, OpeningHours
from locations.items import Feature

# Branch types (/api/branch-types, "short_form") that are post offices run by Pos Malaysia: general post offices,
# post offices, Pos Kiosks (staffed counters in malls, LRT stations and petrol stations), Pos Laju branches and
# Pos Laju service centres. All list letter mail among their services.
POST_OFFICE_TYPES = {"GPO", "PO", "Kiosk", "PPL", "SC"}
# Counters run by third parties: Pos Mini (franchised "mini post offices" operated by entrepreneurs) and authorised
# agents (MyPospay ParcelHub, Collectco and other shops taking parcels and bill payments).
PARTNER_TYPES = {"Mini", "Agent", None}
# Not included: "EDT" (Pos Laju Ezidrive-Thru parcel drop-offs) and "ArRahnu" (Islamic pawnbroking counters).


class PosMalaysiaMYSpider(Spider):
    name = "pos_malaysia_my"
    item_attributes = {"operator": "Pos Malaysia", "operator_wikidata": "Q6112623"}
    allowed_domains = ["www-api.pos.com.my"]
    # The content API behind https://www.pos.com.my/pos-outlet-finder
    api = "https://www-api.pos.com.my/api/outlets?pagination[pageSize]=100&populate=*&pagination[page]="

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(f"{self.api}1", cb_kwargs={"page": 1})

    def parse(self, response: Response, page: int = 1, **kwargs: Any) -> Any:
        data = response.json()
        if page == 1:
            for next_page in range(2, data["meta"]["pagination"]["pageCount"] + 1):
                yield JsonRequest(f"{self.api}{next_page}", cb_kwargs={"page": next_page})

        for outlet in data["data"]:
            attrs = outlet["attributes"]
            if attrs.get("status") == "Non Active":
                continue
            branch_type = ((attrs.get("branch_type") or {}).get("data") or {}).get("attributes", {}).get("short_form")
            if branch_type not in POST_OFFICE_TYPES and branch_type not in PARTNER_TYPES:
                continue

            item = Feature()
            item["ref"] = str(outlet["id"])
            lat, lon = attrs.get("latitude"), attrs.get("longitude")
            # A few agents have garbled coordinates (longitude in the latitude field, or both the same number).
            if lat is not None and lon is not None and 0.5 < lat < 7.5 and 99 < lon < 119.5:
                item["lat"], item["lon"] = lat, lon
            item["addr_full"] = re.sub(r"\s*\n\s*", ", ", (attrs.get("address") or "").strip())
            item["postcode"] = None if attrs.get("postalcode") in (None, "null") else attrs["postalcode"]
            item["state"] = attrs.get("state")
            # "1 300 300 300" is the national call centre, not the outlet.
            phones = [p for p in (attrs.get(f"phoneNo{i}") for i in (1, 2, 3)) if p and p != "1 300 300 300"]
            item["phone"] = "; ".join(phones) or None
            item["opening_hours"] = self.parse_hours(attrs.get("operating_hours"))
            name = (attrs.get("outlet_name") or "").strip()
            if branch_type in POST_OFFICE_TYPES:
                item["branch"] = name
                apply_category(Categories.POST_OFFICE, item)
            else:
                item["name"] = name
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            yield item

    @staticmethod
    def parse_hours(text: str | None) -> OpeningHours | None:
        # e.g. "Monday: 8.30am - 5.30pm;...;Friday: TIADA;Saturday: 8.30am - 1.00pm" (TIADA/CLOSED = closed)
        if not text:
            return None
        oh = OpeningHours()
        # "24 Hours" is rewritten in 12-hour form, so that it parses alongside the am/pm times.
        oh.add_ranges_from_string(text.replace("24 Hours", "12:00am - 11:59pm"), closed=CLOSED_EN + ["tiada"])
        return oh
