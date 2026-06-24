import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

API_URL = "https://webapi.halkbank.com.tr/api/branch/searchbranch"


class HalkbankTRSpider(Spider):
    name = "halkbank_tr"
    item_attributes = {"brand": "Halkbank", "brand_wikidata": "Q5642504"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url=API_URL,
            data={
                "Latitude": 0,
                "Longitude": 0,
                "CityId": 0,
                "CountyId": 0,
                "SearchType": 1,
                "BranchType": "",
                "BranchCode": 0,
                "Features": [],
            },
            callback=self.parse_branches,
        )
        yield JsonRequest(
            url=API_URL,
            data={
                "Latitude": 0,
                "Longitude": 0,
                "CityId": 0,
                "CountyId": 0,
                "SearchType": 2,
                "BranchType": "-1",
                "BranchCode": 0,
                "Features": [],
            },
            callback=self.parse_atms,
        )

    def parse_branches(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("data", []):
            if location.get("countryName") != "TÜRKİYE":
                continue

            item = self.parse_location(location)
            item["ref"] = "branch-{}-{}".format(location.get("branchCode"), location.get("branchType") or "branch")
            item.pop("name", None)
            item["branch"] = self.clean_branch(location.get("branchName"))
            item["phone"] = self.clean_phone(location.get("phone"))
            apply_yes_no(Extras.WHEELCHAIR, item, self.has_feature(location, "BedenselEngelli"))
            apply_category(Categories.BANK, item)
            yield item

    def parse_atms(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("data", []):
            if location.get("countryName") != "TÜRKİYE":
                continue

            item = self.parse_location(location)
            item["ref"] = "atm-{}".format(location.get("atmCode"))
            item["name"] = location.get("atmName") or self.clean_branch(location.get("branchName"))
            item.pop("phone", None)
            apply_yes_no(Extras.CASH_IN, item, location.get("branchType") != "0")
            apply_yes_no(Extras.CASH_OUT, item, True)
            apply_yes_no(Extras.WHEELCHAIR, item, self.has_feature(location, "BedenselEngelli"))
            apply_category(Categories.ATM, item)
            yield item

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)
        item["addr_full"] = location.get("address")
        item["city"] = location.get("cityName")
        item.pop("country", None)
        item.pop("fax", None)
        item.pop("opening_hours", None)
        item.pop("state", None)

        if location.get("postCode") in ("", "00000", "99999"):
            item.pop("postcode", None)

        return item

    @staticmethod
    def clean_branch(branch: str | None) -> str | None:
        if not branch:
            return None
        return branch.strip().removesuffix(" ŞUBESİ").removesuffix(" ŞB.").removesuffix(" ŞB").strip()

    @staticmethod
    def clean_phone(phone: str | None) -> str | None:
        digits = re.sub(r"\D", "", phone or "")
        return phone if len(digits) == 10 else None

    @staticmethod
    def has_feature(location: dict[str, Any], feature_name: str) -> bool:
        return any(
            feature.get("name") == feature_name and feature.get("value") == 1
            for feature in location.get("features", [])
        )
