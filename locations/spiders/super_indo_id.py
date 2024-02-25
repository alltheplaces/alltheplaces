import json
import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class SuperIndoIDSpider(Spider):
    name = "super_indo_id"
    item_attributes = {"brand": "Super Indo", "brand_wikidata": "Q12518060"}
    start_urls = ["https://www.superindo.co.id/hubungi-kami/lokasi-superindo"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            re.search(r"map\.addLocations\( (\[.+\])\);\n\s+var storeDetailTemplate", response.text).group(1)
        ):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["lat"], item["lon"] = location["coord"].split(",")
            item["addr_full"] = location["address"]
            item["image"] = urljoin("https://www.superindo.co.id/images/gerai/", location["pic"])

            yield item
