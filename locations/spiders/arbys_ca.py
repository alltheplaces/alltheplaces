import json
import re
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.arbys_us import ArbysUSSpider


class ArbysCASpider(Spider):
    name = "arbys_ca"
    item_attributes = ArbysUSSpider.item_attributes

    async def start(self) -> AsyncIterator[JsonRequest]:
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
            if m := re.match(r"(?:Arby’s )?(.+)\s-\s*(\d+)", item.pop("name")):
                item["branch"], item["ref"] = m.groups()
            apply_yes_no(Extras.DELIVERY, item, location.get("allowDelivery"))
            apply_yes_no(Extras.TAKEAWAY, item, location.get("allowTakeWay"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("allowdriveThru"))
            apply_yes_no(Extras.INDOOR_SEATING, item, location.get("allowDineIn"))
            apply_yes_no(Extras.WIFI, item, location.get("allowWifi"))
            yield item
