from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class MegaMgcCoffeeKRSpider(Spider):
    name = "mega_mgc_coffee_kr"
    item_attributes = {
        "brand": "메가MGC커피",
        "brand_wikidata": "Q120998343",
    }

    BASE_URL = "https://www.mega-mgccoffee.com/store/find"
    SIDO_LIST = [
        "서울",
        "경기",
        "인천",
        "강원",
        "광주",
        "대전",
        "대구",
        "부산",
        "울산",
        "세종",
        "경남",
        "경북",
        "전남",
        "전북",
        "충남",
        "충북",
        "제주",
    ]

    async def start(self) -> AsyncIterator[Request]:
        for sido in self.SIDO_LIST:
            yield Request(
                url=f"{self.BASE_URL}/store_area_search.php?store_area_name={sido}",
                callback=self.parse_sigungu,
            )

    def parse_sigungu(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        sigungus = response.xpath("//li[@class='store_area_search_list']/@data-sigungu").getall()
        for sigungu in set(sigungus):
            sigungu = sigungu.strip()
            if not sigungu:
                continue
            yield FormRequest(
                url=f"{self.BASE_URL}/store.php",
                formdata={"sigungu": sigungu},
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        try:
            data = response.json()
        except Exception:
            return

        for pos in data.get("positions") or []:
            if not (ref := pos.get("idx")):
                continue

            lat = pos.get("store_lat")
            lon = pos.get("store_lng")
            if not lat or not lon or lat == "0" or lon == "0":
                continue

            item = Feature()
            item["ref"] = str(ref)

            if branch := pos.get("store_name2"):
                item["branch"] = branch.strip()

            if addr := pos.get("store_address"):
                item["addr_full"] = addr.strip()

            if phone := pos.get("store_tel"):
                phone = phone.strip()
                if phone and phone != "-":
                    item["phone"] = phone

            item["lat"] = lat
            item["lon"] = lon

            apply_yes_no(Extras.WIFI, item, pos.get("store_option1") == "Y")
            apply_yes_no(Extras.PARKING, item, pos.get("store_option6") == "Y")
            apply_yes_no(Extras.OUTDOOR_SEATING, item, pos.get("store_option7") == "Y")
            apply_category(Categories.COFFEE_SHOP, item)

            yield item
