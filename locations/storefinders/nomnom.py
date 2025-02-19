import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response, TextResponse

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


def slugify(s: str) -> str:
    return re.sub(r"\s+", "-", s).casefold()


class NomNomSpider(Spider):
    def parse(self, response: TextResponse) -> Iterable[Request]:
        for state in response.json()["data"]:
            for city in state["cities"]:
                yield response.follow(city["datauri"], callback=self.parse_locations)

    def parse_locations(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["data"][0]["restaurants"]:
            item = DictParser.parse(location)
            item["ref"] = location["extref"]
            item["branch"] = location["name"].removeprefix(location["storename"]).strip()
            item["name"] = location["storename"]

            apply_yes_no(Extras.DELIVERY, item, location["candeliver"])
            apply_yes_no(Extras.TAKEAWAY, item, location["canpickup"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["supportsdrivethru"])

            yield from self.post_process_item(item, response, location)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
