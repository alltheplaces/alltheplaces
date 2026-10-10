from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class AeonCinemaJPSpider(Spider):
    name = "aeon_cinema_jp"
    item_attributes = {
        "brand": "イオンシネマ",
        "brand_wikidata": "Q11285965",
        "extras": {"brand:en": "AEON Cinema", "brand:ja": "イオンシネマ"},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.aeoncinema.com/json/_theaters.json")

    def parse(self, response: Response) -> Any:
        data = response.json()  # ty: ignore[unresolved-attribute]
        for _, prefectures in data.items():
            for prefecture, theaters in prefectures.items():
                for theater in theaters:
                    item = DictParser.parse(theater)
                    item["branch"] = item.pop("name")
                    item["name"] = "イオンシネマ"
                    item["ref"] = theater["theater_id"]
                    item["website"] = theater["schedule"]
                    if twitter := theater.get("x"):
                        item["twitter"] = twitter

                    item["state"] = self.add_prefecture_suffix(prefecture)

                    apply_yes_no("cinema:3D", item, theater["3-D"], False)
                    apply_yes_no("cinema:4DX", item, theater["4DX"], False)
                    apply_yes_no("cinema:dbox", item, theater["D-BOX"], False)
                    apply_yes_no("cinema:dolby_atmos", item, theater["Dolby Atmos"], False)
                    apply_yes_no("cinema:IMAX", item, theater["IMAX"], False)
                    apply_yes_no("cinema:MX4D", item, theater["MX4D"], False)
                    apply_yes_no("cinema:THX", item, theater["THX"], False)

                    apply_category(Categories.CINEMA, item)

                    yield item

    @staticmethod
    def add_prefecture_suffix(prefecture: str) -> str:
        """
        Appends appropriate Japanese administrative suffixes (県, 府, 都, 道)
        to a given Japanese prefecture name without duplicating suffixes.
        """
        name = prefecture.strip()
        if not name or name.endswith(("都", "道", "府", "県")):
            return name

        special_cases = {
            "東京": "東京都",
            "京都": "京都府",
            "大阪": "大阪府",
        }

        return special_cases.get(name, f"{name}県")
