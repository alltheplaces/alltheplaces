import re
from typing import Iterable

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address, merge_address_lines

PROVINCES_URL = "https://kurumsal.sokmarket.com.tr/ajax/servis/sehirler"
DISTRICTS_URL = "https://kurumsal.sokmarket.com.tr/ajax/servis/ilceler?city={province}"
STORES_URL = "https://kurumsal.sokmarket.com.tr/ajax/servis/magazalarimiz?city={province}&district={district}"


class SokTRSpider(scrapy.Spider):
    name = "sok_tr"
    item_attributes = {"brand": "ŞOK", "brand_wikidata": "Q19613992"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        yield scrapy.Request(url=PROVINCES_URL, callback=self.parse_provinces)

    def parse_provinces(self, response):
        for province in response.json()["cities"]:
            yield scrapy.Request(
                url=DISTRICTS_URL.format(province=province), callback=self.parse_districts, meta={"province": province}
            )

    def parse_districts(self, response):
        province = response.meta["province"]
        for district in response.json()["districts"]:
            yield scrapy.Request(
                url=STORES_URL.format(province=province, district=district),
                callback=self.parse_stores,
                meta={"province": province, "district": district},
            )

    def parse_stores(self, response):
        for store in response.json()["response"]["subeler"]:
            item = DictParser.parse(store)
            name, branch_name = self.parse_branch_name(store["name"])

            if name == "ŞOK Mini":
                apply_category(Categories.SHOP_CONVENIENCE, item)

            item["name"] = name
            item["branch"] = branch_name
            # SOK API returns lat and lon in the wrong order
            item["lat"] = self.parse_float(store["lng"])
            item["lon"] = self.parse_float(store["ltd"])
            item["state"] = response.meta["province"]
            item["city"] = response.meta["district"]
            item["country"] = "TR"
            item["phone"] = store.get("phone")
            item["street_address"] = clean_address(store["address"])
            item["addr_full"] = merge_address_lines([item["street_address"], item["city"], item["state"]])

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

        name = "ŞOK"
        try:
            brand_name_i = branch_name.index("ŞOK")
            mini_match = mini_re.search(branch_name)

            if mini_match:
                start, end = mini_match.span()
                branch_name = cut(branch_name, start, end)
                name = "ŞOK Mini"
            else:
                start, end = brand_name_i, brand_name_i + 3
                branch_name = cut(branch_name, start, end)
                name = "ŞOK"

        except ValueError:
            name = "ŞOK"

        return name, branch_name


def cut(text: str, start: int, end: int) -> str:
    part1 = text[:start].strip()
    part2 = text[end:].strip()
    if part1 != "" or part2 != "":
        return part1 + part2
    else:
        return part1 + " " + part2
