import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KasikornBankTHSpider(Spider):
    name = "kasikorn_bank_th"
    item_attributes = {"brand_wikidata": "Q276557"}
    requires_proxy = "TH"

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.kasikornbank.com/th/branch/Pages/result.aspx?qs=branch&qw=&qn=n",
            method="POST",
            callback=self.parse,
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "referer": "https://www.kasikornbank.com/th/branch/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            },
        )

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
