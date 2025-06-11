import json
from typing import Any, Iterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.spiders.arbys_us import ArbysUSSpider


class ArbysCASpider(Spider):
    name = "arbys_ca"
    item_attributes = ArbysUSSpider.item_attributes

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://arbys.ca/asmx/WebMethods.asmx/getMapStoresList",
            data={
                "searchVal": "",
                "latitude": "0",
                "longitude": "0",
                "allowString": "",
                "searchlat": "0",
                "searchlong": "0",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.json()["d"]):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").rsplit("-", 1)[0].removeprefix("Arby’s ")
            yield item
