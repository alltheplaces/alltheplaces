import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KasikornBankTHSpider(Spider):
    name = "kasikorn_bank_th"
    item_attributes = {"brand_wikidata": "Q276557"}
    start_urls = ["https://www.kasikornbank.com/th/branch/Pages/result.aspx?qs=branch&qw=&qn=n"]
    requires_proxy = "TH"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//input[@name="ctl00$PlaceHolderMain$ctl05$hdnBRANCH"]/@value').get()
        ):
            item = Feature()
            item["ref"] = location["cls"]
            item["branch"] = location["hdn"]
            item["lat"] = location["lat"]
            item["lon"] = location["lon"]
            item["addr_full"] = location["adr"]
            item["phone"] = "; ".join(location["tel"].split(","))
            item["website"] = item["extras"]["website:th"] = (
                "https://www.kasikornbank.com/th/branch/Pages/detail.aspx?qs=branch&cz={}".format(location["cls"])
            )
            item["extras"]["website:th"] = (
                "https://www.kasikornbank.com/en/branch/Pages/detail.aspx?qs=branch&cz={}".format(location["cls"])
            )
            apply_category(Categories.BANK, item)
            yield item

        for location in json.loads(response.xpath('//input[@name="ctl00$PlaceHolderMain$ctl05$hdnATM"]/@value').get()):
            item = Feature()
            item["ref"] = location["ky"]
            item["branch"] = location["hdn"]
            item["lat"] = location["lat"]
            item["lon"] = location["lon"]
            item["addr_full"] = location["adr"]
            item["website"] = item["extras"]["website:th"] = (
                "https://www.kasikornbank.com/th/branch/Pages/detail.aspx?qs=atm&cz={}".format(location["ky"])
            )
            item["extras"]["website:th"] = (
                "https://www.kasikornbank.com/en/branch/Pages/detail.aspx?qs=atm&cz={}".format(location["ky"])
            )
            apply_category(Categories.ATM, item)
            yield item
