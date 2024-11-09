import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class SlimChickensGBSpider(Spider):
    name = "slim_chickens_gb"
    item_attributes = {"brand": "Slim Chickens", "brand_wikidata": "Q30647224"}
    start_urls = ["https://www.slimchickens.co.uk/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        textdata = response.text
        data = re.search(r'(?<=:restaurants=")[^"]+', textdata).group(0)
        data = re.sub(r"&quot;", '"', data)
        jsondata = json.loads(data)
        for location in jsondata:
            item = DictParser.parse(location)
            item["branch"] = location["title"]
            item["website"] = location["permalink"]
            # Needs opening hours adding
            yield item
