from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SugiPharmacyJPSpider(Spider):
    name = "sugi_pharmacy_jp"
    brands = [
        {"brand": "阪神調剤薬局", "brand_wikidata": "Q11656952"},
        {"brand": "ジャパン", "brand_wikidata": "Q11309938"},
    ]

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=("https://bff.sugi-net.jp/stores/by-area?page={}".format(page)),
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for loc in response.json()["stores"]:
            if "オープン予定" in loc.get("name"):  # skip future openings
                continue
            loc.update(loc.pop("position"))
            item = DictParser.parse(loc)

            if loc.get("name").startswith("阪神調剤薬局"):
                item.update({"brand": "阪神調剤薬局", "brand_wikidata": "Q11656952"})
            elif loc.get("name").startswith("ジャパン"):
                item.update({"brand": "ジャパン", "brand_wikidata": "Q11309938"})
            else:
                item.update({"brand": "スギ薬局", "brand_wikidata": "Q11311460"})

            item["name"] = item["brand"]

            item["branch"] = loc.get("name").removeprefix("阪神調剤薬局").removeprefix("ジャパン")
            item["website"] = f"https://www.sugi-net.jp/stores/{loc.get('id')}"
            apply_yes_no(Extras.DISPENSING, item, loc.get("isPharmacy"))
            apply_yes_no(Extras.PARKING, item, loc.get("hasParking"))
            if loc["storeInfo"][0]["storeType"] == "sales":
                apply_category(Categories.SHOP_CHEMIST, item)
            else:
                apply_category(Categories.PHARMACY, item)

            yield item

        if len(response.json()["stores"]) >= 10:
            yield self.make_request(response.meta["page"] + 1)
