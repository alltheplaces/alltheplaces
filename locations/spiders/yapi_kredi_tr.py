from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

API_URL = "https://www.yapikredi.com.tr/_ajaxproxy/general.aspx"
PAGE_SIZE = 10


class YapiKrediTRSpider(Spider):
    name = "yapi_kredi_tr"
    item_attributes = {"brand": "Yapı Kredi", "brand_wikidata": "Q8049138"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url=f"{API_URL}/FetchCity", data={}, callback=self.parse_cities)

    def parse_cities(self, response: Response, **kwargs: Any) -> Any:
        for city in response.json()["d"]["Data"].get("Parameters", []):
            city_id = city["Key"]
            city_name = city["Value"]

            yield JsonRequest(
                url=f"{API_URL}/FetchBranchByFilter",
                data={
                    "cityId": city_id,
                    "districtId": None,
                    "keyword": None,
                    "branchTypes": None,
                    "functions": [],
                    "page": 1,
                },
                callback=self.parse_branches,
                cb_kwargs={"city_id": city_id, "city_name": city_name, "page": 1},
            )
            yield JsonRequest(
                url=f"{API_URL}/FetchAtmByFilter",
                data={
                    "cityId": city_id,
                    "town": None,
                    "keyword": None,
                    "properties": [],
                    "page": 1,
                },
                callback=self.parse_atms,
                cb_kwargs={"city_id": city_id, "city_name": city_name, "page": 1},
            )

    def parse_branches(self, response: Response, city_id: str, city_name: str, page: int, **kwargs: Any) -> Any:
        data = response.json()["d"]["Data"]
        locations = data.get("BranchList") or []

        for location in locations:
            item = self.parse_branch(location, city_name)
            apply_category(Categories.BANK, item)
            yield item

        if locations and page * PAGE_SIZE < data.get("TotalCount", 0):
            yield JsonRequest(
                url=f"{API_URL}/FetchBranchByFilter",
                data={
                    "cityId": city_id,
                    "districtId": None,
                    "keyword": None,
                    "branchTypes": None,
                    "functions": [],
                    "page": page + 1,
                },
                callback=self.parse_branches,
                cb_kwargs={"city_id": city_id, "city_name": city_name, "page": page + 1},
            )

    def parse_atms(self, response: Response, city_id: str, city_name: str, page: int, **kwargs: Any) -> Any:
        data = response.json()["d"]["Data"]
        locations = data.get("NearestATM") or []

        for location in locations:
            if location.get("NotPublic"):
                continue

            item = self.parse_atm(location, city_name)
            apply_yes_no(Extras.CASH_IN, item, location.get("DepositNotAvailable") is False)
            apply_yes_no(
                Extras.CASH_OUT,
                item,
                bool(location.get("WithdrawalDefinedCurrencies") or location.get("WithdrawalAvailableCurrencies")),
            )
            apply_yes_no(Extras.WHEELCHAIR, item, location.get("DisabledCompatible") is True)
            apply_category(Categories.ATM, item)
            yield item

        if locations and page * PAGE_SIZE < data.get("TotalCount", 0) and len(locations) == PAGE_SIZE:
            yield JsonRequest(
                url=f"{API_URL}/FetchAtmByFilter",
                data={
                    "cityId": city_id,
                    "town": None,
                    "keyword": None,
                    "properties": [],
                    "page": page + 1,
                },
                callback=self.parse_atms,
                cb_kwargs={"city_id": city_id, "city_name": city_name, "page": page + 1},
            )

    def parse_branch(self, location: dict[str, Any], city_name: str) -> Feature:
        item = DictParser.parse(location)
        item["ref"] = location.get("BranchCode")
        item["addr_full"] = location.get("Address")
        item["city"] = city_name

        if branch := item.pop("name", None):
            item["branch"] = branch.removesuffix(" ŞUBESİ").strip()

        item.pop("fax", None)

        return item

    def parse_atm(self, location: dict[str, Any], city_name: str) -> Feature:
        item = DictParser.parse(location)
        item["ref"] = location.get("TerminalID")
        item["addr_full"] = location.get("Address")
        item["city"] = city_name

        if location.get("StartWorkingHour") and location.get("EndWorkingHour"):
            item["opening_hours"] = "Mo-Su {}-{}".format(location["StartWorkingHour"], location["EndWorkingHour"])

        return item
