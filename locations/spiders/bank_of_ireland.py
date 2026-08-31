import base64
import json
import re
import zlib
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class BankOfIrelandSpider(Spider):
    name = "bank_of_ireland"
    item_attributes = {"brand": "Bank of Ireland", "brand_wikidata": "Q806689"}
    atm_locations_url = (
        "https://personalbanking.bankofireland.com/ways-to-bank/branch-banking/external-lodgement-atm-locations/"
    )

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.atm_locations_url, callback=self.parse_atm_locations)

    def parse_atm_locations(self, response: Response, **kwargs: Any) -> Any:
        atm_slugs = set()
        for href in response.xpath('//a[contains(@href, "/branch-locator/")]/@href').getall():
            if slug := urlparse(href).path.strip("/").removeprefix("branch-locator/").strip("/"):
                atm_slugs.add(slug)

        yield Request(
            "https://www.bankofireland.com/branch-locator/",
            callback=self.parse_locations,
            cb_kwargs={"atm_slugs": atm_slugs},
        )

    def parse_locations(self, response: Response, atm_slugs: set[str], **kwargs: Any) -> Any:
        config = self.decode_config(response)
        for branch in config["branches"].values():
            item = self.parse_branch(branch, atm_slugs)
            apply_category(Categories.BANK, item)
            yield Request(item["website"], callback=self.parse_branch_page, cb_kwargs={"item": item})

        for atm in config.get("atms", {}).values():
            item = self.parse_atm(atm)
            apply_category(Categories.ATM, item)
            yield item

    def parse_branch_page(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        if description := response.xpath('//*[@id = "meta-description"]/@content').get():
            if match := re.search(r"\bBOI Direct:\s*([^.]*)", description):
                item["phone"] = match.group(1).strip()
        yield item

    def parse_branch(self, branch: dict[str, Any], atm_slugs: set[str]) -> Feature:
        item = DictParser.parse(branch)
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removesuffix(" (Outlet)")
        item["website"] = "https://www.bankofireland.com/branch-locator/{}/".format(branch["slug"])
        item["country"] = self.country_code(branch)

        if branch.get("elatm") or branch["slug"] in atm_slugs:
            apply_yes_no(Extras.ATM, item, True)
            apply_yes_no(Extras.CASH_IN, item, True)
            apply_yes_no(Extras.CASH_OUT, item, True)

        return item

    def parse_atm(self, atm: dict[str, Any]) -> Feature:
        item = DictParser.parse(atm)
        item["branch"] = item.pop("name", None)
        item["website"] = "https://www.bankofireland.com/branch-locator/"
        item["country"] = self.country_code(atm)
        apply_yes_no(Extras.CASH_OUT, item, True)
        return item

    def decode_config(self, response: Response) -> dict[str, Any]:
        if match := re.search(r'window\.DATA_INIT = "([\s\S]*?)";', response.text):
            data = base64.b64decode(match.group(1).replace(r"\/", "/"))
            return json.loads(zlib.decompress(data))
        self.logger.error("Unable to find DATA_INIT on {}".format(response.url))
        return {"branches": {}, "atms": {}}

    def country_code(self, location: dict[str, Any]) -> str:
        details = location.get("details")
        if isinstance(details, dict) and details.get("bic") == "BOFI GB2B":
            return "GB"
        if "Northern Ireland" in location.get("address", ""):
            return "GB"
        return "IE"
