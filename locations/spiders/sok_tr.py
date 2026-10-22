import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SokTRSpider(Spider):
    name = "sok_tr"
    item_attributes = {"brand": "Şok", "brand_wikidata": "Q19613992"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    STORES_API = "https://kurumsal.sokmarket.com.tr/api/public/stores"
    start_urls = [f"{STORES_API}/cities"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for province in response.json()["cities"]:
            yield JsonRequest(
                url=f"{self.STORES_API}?city={province}",
                callback=self.parse_stores,
                cb_kwargs=dict(province=province),
            )

    def parse_stores(self, response: Response, province: str) -> Iterable[Feature]:
        for store in response.json().get("subeler", []):
            item = DictParser.parse(store)
            name, branch_name = self.parse_branch_name(store["name"])

            item["name"] = name
            item["branch"] = branch_name
            # SOK API returns lat and lon in the wrong order
            item["lat"] = self.parse_float(store["lng"])
            item["lon"] = self.parse_float(store["ltd"])
            item["state"] = province
            item["city"] = store.get("ilce")
            item["phone"] = store.get("phone")
            item["street_address"] = clean_address(item.pop("addr_full", store["address"]))
            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

    @staticmethod
    def parse_float(n: str) -> float:
        try:
            return float(n.replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def parse_branch_name(branch_name: str) -> tuple[str, str]:
        mini_re = re.compile(r"ŞOK.[\s]*MİNİ")
        branch_name = branch_name.strip().removesuffix("MAĞAZASI").strip()

        name = "Şok"
        try:
            brand_name_i = branch_name.index("ŞOK")
            mini_match = mini_re.search(branch_name)

            if mini_match:
                start, end = mini_match.span()
                branch_name = cut(branch_name, start, end)
                name = "Şok Mini"
            else:
                start, end = brand_name_i, brand_name_i + 3
                branch_name = cut(branch_name, start, end)
                name = "Şok"

        except ValueError:
            name = "Şok"

        return name, branch_name


def cut(text: str, start: int, end: int) -> str:
    part1 = text[:start].strip()
    part2 = text[end:].strip()
    if part1 != "" or part2 != "":
        return part1 + part2
    else:
        return part1 + " " + part2
