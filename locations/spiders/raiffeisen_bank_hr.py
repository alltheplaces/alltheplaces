from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class RaiffeisenBankHRSpider(Spider):
    name = "raiffeisen_bank_hr"
    item_attributes = {"brand": "Raiffeisen bank", "brand_wikidata": "Q125756787"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.rba.hr/hr_HR/lokacije-poslovnice-bankomati?p_p_id=poslovnice_WAR_poslovniceportlet&p_p_lifecycle=2&p_p_resource_id=loadLocations&p_p_cacheability=cacheLevelPage"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            if street_address := item.pop("addr_full", None):
                item["street_address"] = street_address

            location_type = location.get("type", {})
            has_branch = any(location_type.get(key) for key in ("branch", "premium", "business"))
            has_atm = location_type.get("atmWithdrawal") or location_type.get("atmDeposit")

            if has_branch:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, has_atm)
            elif has_atm:
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, location_type.get("atmDeposit"))
            else:
                self.logger.warning("Skipping location with unexpected type: {}".format(location_type))
                continue

            yield item
