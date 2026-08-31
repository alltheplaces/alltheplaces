from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class DskBankBGSpider(Spider):
    name = "dsk_bank_bg"
    item_attributes = {"brand": "Банка ДСК", "brand_wikidata": "Q5206146"}
    allowed_domains = ["dskbank.bg"]
    start_urls = ["https://dskbank.bg/GetOfficesData?cultureName=bg"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json():
            item = DictParser.parse(data)
            item["phone"] = None
            item["ref"] = data["Signature"] or data["office_serviceId"]
            item["street_address"] = data["office_address"]
            item["lat"] = data["office_latitude"]
            item["lon"] = data["office_longitude"]

            if "Branch" in data["office_type"]:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "Atm" in data["office_type"])

                oh = OpeningHours()
                oh_string = (data.get("OpenHours") or "").replace("ч.", "").replace("<br>", "")
                oh.add_ranges_from_string(oh_string, days=DAYS_BG)
                item["opening_hours"] = oh

            elif data["office_type"] == ["Atm"]:
                apply_category(Categories.ATM, item)

            yield item
