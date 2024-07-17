import string
from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class OTacosSpider(Spider):
    name = "o_tacos"
    item_attributes = {"brand": "O'Tacos", "brand_wikidata": "Q28494040"}

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            "https://www.o-tacos.fr/ajax",
            formdata={"action": "store_wpress_listener", "method": "display_map", "nb_display": "5000"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = string.capwords(item.pop("name"))

            yield item
