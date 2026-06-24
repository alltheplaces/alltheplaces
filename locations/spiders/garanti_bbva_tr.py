from typing import Any, AsyncIterator
from uuid import uuid4

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class GarantiBbvaTRSpider(Spider):
    name = "garanti_bbva_tr"
    item_attributes = {"brand": "Garanti Bankası", "brand_wikidata": "Q322962"}

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(
            url="https://customers.garantibbva.com.tr/digital-public/public-atm-branch-ch/v0/branches",
            headers=self.api_headers(),
            cb_kwargs={"ref_prefix": "branch"},
        )
        yield JsonRequest(
            url="https://customers.garantibbva.com.tr/digital-public/public-atm-branch-ch/v0/atms",
            headers=self.api_headers(),
            cb_kwargs={"ref_prefix": "atm"},
        )

    def parse(self, response: Response, ref_prefix: str, **kwargs: Any) -> Any:
        for location in response.json():
            item = self.parse_location(location, ref_prefix)

            if ref_prefix == "atm":
                apply_yes_no(Extras.CASH_IN, item, bool(location.get("deposit")))
                apply_yes_no(Extras.CASH_OUT, item, bool(location.get("withdraw")))
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)

            if "orthopedic" in location.get("accessible", []):
                apply_yes_no(Extras.WHEELCHAIR, item, True)

            yield item

    def parse_location(self, location: dict[str, Any], ref_prefix: str) -> Feature:
        item = DictParser.parse(location)
        item["ref"] = f"{ref_prefix}-{location['id']}"

        if name := item.pop("name", None):
            item["branch"] = name.removeprefix(f"{location['id']} - ").strip()

        item["street_address"] = item.pop("addr_full", None)
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item.pop("fax", None)

        return item

    def api_headers(self) -> dict[str, str]:
        guid = uuid4().hex
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "channel": "Internet",
            "ip": "127.0.0.1",
            "dialect": "TR",
            "guid": guid,
            "tenant-company-id": "GAR",
            "x-client-trace-id": guid,
            "client-session-id": uuid4().hex[:20],
            "client-type": "ArkClient",
            "client-id": "DslahJXaDW59ibNZppCm",
            "tenant-geolocation": "TUR",
            "Referer": "https://webforms.garantibbva.com.tr/public-atm-branch-app/?lang=en",
        }
