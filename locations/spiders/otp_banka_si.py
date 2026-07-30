from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class OtpBankaSISpider(Spider):
    name = "otp_banka_si"
    item_attributes = {"brand": "OTP banka", "brand_wikidata": "Q140373875"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.otpbanka.si/jsonatmsoffices.ashx?localeid=sl-SI")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        # "pbsoffices" are Pošta Slovenije post offices (partner banking), not OTP branches -> skipped.
        for office in data["nkbmoffices"]:
            # DictParser maps id->ref, title->name, address->addr_full, zip->postcode, city, lat/lng->lat/lon
            item = DictParser.parse(office)
            item["street_address"] = item.pop("addr_full", None)
            item["branch"] = item.pop("name").removeprefix("POSLOVALNICA ")
            apply_category(Categories.BANK, item)
            yield item
        for atm in data["atms"]:
            item = DictParser.parse(atm)  # standalone ATM keeps the host-venue title as name
            item["street_address"] = item.pop("addr_full", None)
            properties = atm.get("properties") or ""  # e.g. "rfid,automaticdeposit"
            apply_yes_no(Extras.CASH_IN, item, "automaticdeposit" in properties)
            apply_yes_no(PaymentMethods.CONTACTLESS, item, "rfid" in properties)
            apply_category(Categories.ATM, item)
            yield item
