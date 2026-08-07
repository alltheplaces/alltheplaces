import json
import re
from typing import Any

from requests import Response

from locations.storefinders.stockinstore import DictParser, Spider


class LasikPlusUSSpider(Spider):
    name = "lasik_plus_us"
    item_attributes = {"brand": "LasikPlus", "brand_wikidata": "Q126111242"}
    start_urls = ["https://www.lasikplus.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        json_data = json.loads(
            re.search(
                r"locationsData\s*=\s*(\[.+\]);\s*\/\/",
                response.xpath('//*[@ id="meta-locations-map-js-extra"]/text()').get(),
            ).group(1)
        )
        for location in json_data:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            item["website"] = location.get("link")
            yield item
