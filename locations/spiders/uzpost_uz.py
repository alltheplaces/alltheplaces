import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response
from shapely.geometry import Point, Polygon

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class UzpostUZSpider(Spider):
    name = "uzpost_uz"
    item_attributes = {"operator": "UzPost", "operator_wikidata": "Q105227651"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://new.pochta.uz/api/v1/maps/new/post/offices/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The list only carries coordinates and service flags; names and addresses come from the detail endpoint.
        for office in response.json()["result"]:
            yield JsonRequest(
                url="https://new.pochta.uz/api/v1/maps/new/post/offices/detail/{}/".format(office["index"]),
                callback=self.parse_office,
            )

    def parse_office(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()["result"]
        office = result["postal_office"]
        item = DictParser.parse(office)
        item["ref"] = office["index"]
        item["branch"] = (office["name_uz"] or "").removeprefix("UzPost - ") or None
        # "city" mixes region, district and town names, and "region" spells the same region in Uzbek Latin,
        # Uzbek Cyrillic, Russian or English (e.g. "Тошкент" / "Ташкент" / "Tashkent"), so neither is mapped.
        item.pop("city", None)
        item.pop("state", None)
        if office["house"] and re.search(r"\d", office["house"]):  # also "Рақамсиз" / "yo'q" (no number)
            item["housenumber"] = office["house"]
        # The index is the postcode of the delivery area returned with the office; some offices sit outside it.
        area = (result.get("locations") or {}).get("locations") or []
        try:
            if len(area) > 2 and Polygon(area).contains(Point(float(office["lat"]), float(office["lng"]))):
                item["postcode"] = office["index"]
        except ValueError:  # malformed source coordinates, e.g. "67.272688,370"; the pipeline drops the geometry
            pass
        apply_category(Categories.POST_OFFICE, item)
        yield item
