from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

API_URL = "https://daisosangyo.locationsmart.org/map/g2?n=90&s=0&w=0&e=179&z=99"
DETAIL_URL_TEMPLATE = "https://www.daiso-sangyo.co.jp/shop/detail/{shop_id}"


class DaisoSangyoJPSpider(Spider):
    name = "daiso_sangyo_jp"
    allowed_domains = ["daisosangyo.locationsmart.org", "www.daiso-sangyo.co.jp"]

    # brand_id -> (brand name, wikidata id). CouCou has no wikidata item.
    BRANDS = {
        "daiso": ("ダイソー", "Q866991"),
        "threeppy": ("THREEPPY", "Q137916752"),
        "sp": ("Standard Products", "Q137916628"),
        "coucou": ("CouCou", None),
    }

    # Store names start with the brand prefix, the rest is the branch name,
    # e.g. "DAISO マルナカ三田店" -> branch "マルナカ三田店".
    BRAND_PREFIXES = {
        "daiso": "DAISO ",
        "threeppy": "THREEPPY ",
        "sp": "Standard Products ",
        "coucou": "CouCou ",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=API_URL)

    def parse(self, response: Response) -> Iterable[Request]:
        for shop in response.json()["shops"]:
            yield Request(
                url=DETAIL_URL_TEMPLATE.format(shop_id=shop["id"]), callback=self.parse_store, cb_kwargs={"shop": shop}
            )

    def parse_store(self, response: Response, shop: dict) -> Feature:
        item = Feature()
        item["ref"] = shop["id"]
        item["branch"] = shop["name"].removeprefix(self.BRAND_PREFIXES[shop["brand_id"]])
        item["lat"] = shop["lat"]
        item["lon"] = shop["lon"]
        item["website"] = DETAIL_URL_TEMPLATE.format(shop_id=shop["id"])

        address = "".join(response.xpath('//dt[text()="住所"]/following-sibling::dd[1]//text()').getall()).strip()
        if address:
            item["addr_full"] = address

        brand_name, wikidata = self.BRANDS[shop["brand_id"]]
        item["brand"] = brand_name
        if wikidata:
            item["brand_wikidata"] = wikidata
        if shop["brand_id"] != "daiso":
            # daiso is in NSI which supplies its name
            item["name"] = brand_name

        item["opening_hours"] = self.parse_hours(shop["hours"])

        apply_category(Categories.SHOP_VARIETY_STORE, item)

        yield item

    @staticmethod
    def parse_hours(value: str) -> OpeningHours:
        opening_hours = OpeningHours()
        open_time, close_time = value.split("-", 1)
        opening_hours.add_days_range(DAYS, open_time, close_time)
        return opening_hours
